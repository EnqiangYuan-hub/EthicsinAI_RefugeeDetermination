# ============================================================
# Synthetic RSD Dataset Generator
# Refugee Status Determination AI Case Study
# ============================================================
#
# DESIGN NOTES (for instructors):
# This dataset intentionally encodes several known biases found in
# real automated RSD systems, drawn from the literature:
#
#   1. CREDIBILITY BIAS: Credibility scores are partly driven by
#      language proficiency and education. This reflects a documented
#      flaw in real systems — formal expression is rewarded, even though
#      trauma, culture, and circumstance affect how people communicate.
#      (Kinchin & Mougouei, 2022; Kasapoglu et al., 2021)
#
#   2. TRAUMA PENALTY: Applicants with reported trauma have slightly
#      lower credibility scores, mimicking how inconsistent or fragmented
#      testimony (a common trauma response) is penalized in assessments.
#
#   3. COUNTRY-OF-ORIGIN BIAS: Risk scores vary by country, reflecting
#      both real conflict data AND the way COI can encode systemic assumptions.
#
#   4. AUTOMATION BIAS: The human override rate is low (10%), and overrides
#      only partially correct AI errors, reflecting "rubber-stamping" dynamics.
#
# These are intentional pedagogical features, not bugs.
# ============================================================

import pandas as pd
import numpy as np

np.random.seed(42)

# ============================================================
# PART 1 — APPLICANT INPUTS
# ============================================================

n = 500

countries = ["Syria", "Afghanistan", "Sudan", "Myanmar", "Eritrea", "Venezuela", "Iraq", "Somalia"]
genders = ["Male", "Female", "Non-binary"]
education_levels = ["None", "Primary", "Secondary", "Tertiary"]
language_levels = ["None", "Basic", "Intermediate", "Advanced", "Fluent"]
persecution_grounds = ["race", "religion", "nationality", "political_opinion", "social_group"]
persecution_types = ["violence", "detention", "threats", "sexual_violence", "discrimination"]

df = pd.DataFrame({
    "id": range(1, n + 1),
    "country_of_origin": np.random.choice(countries, n),
    # Gender sampling reflects approximate real-world RSD demographics.
    # Non-binary/gender-nonconforming claimants are a small but recognized
    # population under the 1951 Convention's "particular social group" ground.
    # Set to ~4% to mirror real caseload proportions — this intentionally
    # surfaces the underrepresentation problem in algorithmic audits.
    "gender": np.random.choice(genders, n, p=[0.48, 0.48, 0.04]),
    "age": np.random.randint(18, 65, n),
    "education_level": np.random.choice(education_levels, n, p=[0.1, 0.3, 0.4, 0.2]),
    "language_proficiency": np.random.choice(language_levels, n, p=[0.05, 0.25, 0.4, 0.2, 0.1]),
    "family_size": np.random.randint(1, 7, n),
    "prior_camp_years": np.random.randint(0, 10, n),
    "persecution_ground": np.random.choice(persecution_grounds, n),
    "persecution_type": np.random.choice(persecution_types, n),
})

df["nexus_established"] = np.random.choice([True, False], n, p=[0.7, 0.3])

# State protection: floor at 0.05 to avoid artifactual exact-zero values
df["state_protection_score"] = np.clip(np.random.normal(0.3, 0.15, n), 0.05, 1.0)

df["internal_relocation_possible"] = np.random.choice([True, False], n, p=[0.4, 0.6])

# Trauma indicator — reflects literature showing trauma affects testimony quality
# Higher rates for conflict-heavy regions and gendered persecution types
trauma_base = np.where(
    df["country_of_origin"].isin(["Syria", "Afghanistan", "Eritrea", "Somalia"]), 0.65, 0.40
)
trauma_base = np.where(
    df["persecution_type"].isin(["sexual_violence", "detention"]),
    np.minimum(trauma_base + 0.15, 0.85),
    trauma_base
)
df["reported_trauma"] = np.random.binomial(1, trauma_base).astype(bool)

# ============================================================
# PART 2 — SCORING FUNCTIONS
# ============================================================

# --- Credibility Score ---
# Intentional bias: language and education inflate credibility.
# Trauma REDUCES credibility slightly — reflecting how fragmented or
# inconsistent trauma-affected testimony is penalized in real systems.
# This is a documented flaw, not a correct design choice.

language_map = {"None": -0.20, "Basic": -0.10, "Intermediate": 0.0, "Advanced": +0.05, "Fluent": +0.10}
edu_map      = {"None": -0.10, "Primary": 0.0,  "Secondary": +0.05, "Tertiary": +0.10}

base_cred    = np.random.normal(0.65, 0.15, n)
lang_effect  = df["language_proficiency"].map(language_map).values
edu_effect   = df["education_level"].map(edu_map).values
trauma_penalty = np.where(df["reported_trauma"], -0.08, 0.0)   # <-- intentional bias

df["credibility_score"] = np.clip(base_cred + lang_effect + edu_effect + trauma_penalty, 0.0, 1.0)

# --- Risk Score ---
# NOT capped at 1.0 before normalization — avoids invisible data artifacts.
# Represents severity of persecution risk in country of origin.

risk_means = {
    "Syria": 0.85, "Afghanistan": 0.80, "Sudan": 0.75, "Myanmar": 0.70,
    "Eritrea": 0.70, "Venezuela": 0.55, "Iraq": 0.65, "Somalia": 0.78
}
ptype_map = {
    "violence": +0.10, "detention": +0.05, "threats": 0.0,
    "sexual_violence": +0.15, "discrimination": -0.05
}
gender_map = {"Male": 0.0, "Female": +0.08, "Non-binary": +0.06}

base_risk      = df["country_of_origin"].map(risk_means).values
ptype_effect   = df["persecution_type"].map(ptype_map).values
gender_effect  = df["gender"].map(gender_map).values
noise          = np.random.normal(0, 0.05, n)

# Allow scores above 1.0 before clipping so the cap is visible/documented
raw_risk = base_risk + ptype_effect + gender_effect + noise
df["risk_score"] = np.clip(raw_risk, 0.0, 1.0)
df["risk_score_uncapped"] = raw_risk  # kept for transparency; students can examine capping effects

# --- Integration Score ---
df["integration_score"] = np.clip(
    0.4 * df["credibility_score"]
    + 0.2 * (1 - abs(df["age"] - 35) / 35)
    + 0.4 * np.random.random(n),
    0.0, 1.0
)

# ============================================================
# PART 3 — AI DECISION LOGIC
# ============================================================
# Threshold rule: approve if risk is high (real danger exists) AND
# credibility clears a minimum bar. Nexus and state protection also factor in.
# This produces a ~55-60% approval rate, closer to real-world figures.

approve_score = (
    0.45 * df["risk_score"]
    + 0.30 * df["credibility_score"]
    + 0.15 * df["nexus_established"].astype(float)
    + 0.10 * (1 - df["state_protection_score"])
)

# Threshold tuned to produce ~55-60% approval rate.
# risk_score is high for most conflict countries, so we require nexus AND
# credibility to both clear reasonable bars to avoid near-universal approval.
df["AI_decision"] = np.where(
    (approve_score > 0.62)
    & (df["credibility_score"] > 0.50)
    & (df["nexus_established"] == True),
    "approve",
    "deny"
)

# ============================================================
# PART 4 — HUMAN-IN-THE-LOOP OVERSIGHT
# ============================================================
# ~10% of cases flagged for human review.
# Of reviewed cases, ~50% result in a flipped decision (human override).
# This is intentionally low — reflects automation bias literature
# where human reviewers tend to defer to the algorithm.

df["human_reviewed"] = False
df["human_override"] = False

reviewed_idx = np.random.choice(df.index, size=int(0.10 * n), replace=False)
df.loc[reviewed_idx, "human_reviewed"] = True

# Of reviewed cases, flip ~50%
flip_mask = (df["human_reviewed"]) & (np.random.rand(n) < 0.50)
df.loc[flip_mask, "human_override"] = True

# Build final_decision: start from AI, apply flips where overridden
df["final_decision"] = df["AI_decision"].copy()
flip_idx = df[df["human_override"]].index
df.loc[flip_idx, "final_decision"] = df.loc[flip_idx, "AI_decision"].apply(
    lambda x: "deny" if x == "approve" else "approve"
)

# Processing time: base 30-120 days, +20-60 if human reviewed
base_time = np.random.randint(30, 120, n)
review_delay = np.where(df["human_reviewed"], np.random.randint(20, 60, n), 0)
df["processing_time_days"] = base_time + review_delay

# ============================================================
# PART 5 — APPEALS & BIAS AUDIT
# ============================================================

# 30% of denied applicants appeal
appeal_rand = np.random.rand(n)
df["appealed"] = (df["final_decision"] == "deny") & (appeal_rand < 0.30)

# 40% of appeals are overturned
appeal_outcomes = []
for _, row in df.iterrows():
    if not row["appealed"]:
        appeal_outcomes.append("N/A")
    elif np.random.rand() < 0.40:
        appeal_outcomes.append("overturned")
    else:
        appeal_outcomes.append("upheld")
df["appeal_outcome"] = appeal_outcomes

# Bias flag — simulate a fairness audit
# Bias is more likely when trauma was present but credibility was low,
# or when nexus was established but case was still denied.
bias_probs = []
for _, row in df.iterrows():
    if row["reported_trauma"] and row["credibility_score"] < 0.5:
        bias_probs.append(np.random.choice(["none", "moderate", "severe"], p=[0.40, 0.40, 0.20]))
    elif row["nexus_established"] and row["final_decision"] == "deny":
        bias_probs.append(np.random.choice(["none", "moderate", "severe"], p=[0.50, 0.35, 0.15]))
    else:
        bias_probs.append(np.random.choice(["none", "moderate", "severe"], p=[0.80, 0.15, 0.05]))
df["bias_flag"] = bias_probs

# ============================================================
# PART 6 — COLUMN ORDER & EXPORT
# ============================================================

column_order = [
    # Applicant inputs
    "id", "country_of_origin", "gender", "age",
    "education_level", "language_proficiency",
    "family_size", "prior_camp_years",
    "persecution_ground", "persecution_type",
    "nexus_established", "state_protection_score",
    "internal_relocation_possible", "reported_trauma",
    # Scores
    "credibility_score", "risk_score", "risk_score_uncapped", "integration_score",
    # System process
    "AI_decision", "human_reviewed", "human_override",
    "final_decision", "processing_time_days",
    # Outcomes
    "appealed", "appeal_outcome", "bias_flag"
]

df = df[column_order]

# Quick sanity check
print("=== Dataset Summary ===")
print(f"Shape: {df.shape}")
print(f"\nAI Decision distribution:\n{df['AI_decision'].value_counts()}")
print(f"\nFinal Decision distribution:\n{df['final_decision'].value_counts()}")
print(f"\nApproval rate by country (final_decision):")
print(df.groupby("country_of_origin")["final_decision"]
      .apply(lambda x: (x == "approve").mean())
      .round(2))
print(f"\nAppeals filed: {df['appealed'].sum()}")
print(f"Appeals overturned: {(df['appeal_outcome'] == 'overturned').sum()}")
print(f"\nBias flag distribution:\n{df['bias_flag'].value_counts()}")
print(f"\nTrauma rate: {df['reported_trauma'].mean():.1%}")
print(f"\nCases where trauma present but credibility < 0.5: {((df['reported_trauma']) & (df['credibility_score'] < 0.5)).sum()}")

df.to_csv("synthetic_RSD_dataset.csv", index=False)
print("\nSaved to synthetic_RSD_dataset.csv")
