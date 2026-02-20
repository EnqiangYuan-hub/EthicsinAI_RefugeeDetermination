# CODEBOOK: Synthetic Refugee Status Determination (RSD) Dataset

**Project:** AI Decision-Making in Refugee Status Determination Case Study  
**Institution:** Duke University, Mechanical Engineering & Materials Science  
**Dataset file:** `RefugeeProfile.csv`  
**Rows:** 500 | **Columns:** 26 | **Random seed:** 42

---

## Background

This dataset simulates the **Refugee Status Determination (RSD)** process — the legal procedure used by UNHCR and national governments to decide whether a person qualifies for refugee protection under the [1951 Refugee Convention](https://www.unhcr.org/en-us/1951-refugee-convention.html).

To be recognized as a refugee, an applicant must demonstrate:

1. A well-founded **fear of persecution**
2. Based on one of five protected grounds: **race, religion, nationality, political opinion, or membership in a particular social group**
3. That their **home country cannot or will not protect them**
4. That **internal relocation** within their country is not a safe option

This dataset models an AI system that scores applicants on these criteria and produces an approval/denial decision, followed by a human review stage.

---

## Intentional Bias Design (Pedagogical Features)

> This dataset intentionally encodes biases documented in real automated RSD systems. 

| Bias | How It Is Encoded | Why It Matters |
|------|-------------------|----------------|
| **Credibility bias** | `credibility_score` is partly driven by `language_proficiency` and `education_level` | Formal expression is rewarded even though trauma, culture, and circumstance affect how people communicate (Kinchin & Mougouei, 2022) |
| **Trauma penalty** | `reported_trauma = True` reduces `credibility_score` by ~0.08 | Inconsistent or fragmented testimony — a common trauma response — is penalized in automated systems |
| **Country-of-origin assumptions** | `risk_score` varies by country of origin | Risk scores reflect both real conflict data and the way COI data can encode systemic assumptions about certain nationalities |
| **Automation bias** | Only 10% of cases receive human review; overrides only partially correct errors | Reflects documented "rubber-stamping" dynamics in human-in-the-loop systems (NYSBA, 2022) |
| **Underrepresentation** | Non-binary applicants comprise ~4% of the dataset | Mirrors real RSD caseload proportions; intentionally surfaces how small groups become invisible in algorithmic audits |

---

## Variable Reference

### Section 1 — Applicant Demographics

| Variable | Type | Values | Notes |
|----------|------|--------|-------|
| `id` | Integer | 1–500 | Unique applicant identifier |
| `country_of_origin` | Categorical | Syria, Afghanistan, Sudan, Myanmar, Eritrea, Venezuela, Iraq, Somalia | Eight countries with active displacement crises as of 2024 |
| `gender` | Categorical | Male, Female, Non-binary | Sampled at ~48% / 48% / 4% to reflect real RSD demographics. Non-binary/gender-nonconforming claimants are a recognized population under the "particular social group" persecution ground. |
| `age` | Integer | 18–64 | Adult applicants only |
| `education_level` | Categorical | None, Primary, Secondary, Tertiary | Sampled: 10% None, 30% Primary, 40% Secondary, 20% Tertiary |
| `language_proficiency` | Categorical | None, Basic, Intermediate, Advanced, Fluent | Proficiency in the language of the receiving country. Sampled: 5% / 25% / 40% / 20% / 10% |
| `family_size` | Integer | 1–6 | Number of family members in the applicant's unit |
| `prior_camp_years` | Integer | 0–9 | Years spent in a refugee camp before this application |

---

### Section 2 — Legal Claim Variables

| Variable | Type | Values | Notes |
|----------|------|--------|-------|
| `persecution_ground` | Categorical | race, religion, nationality, political_opinion, social_group | The basis of the persecution claim under the 1951 Convention |
| `persecution_type` | Categorical | violence, detention, threats, sexual_violence, discrimination | The form of harm experienced or feared |
| `nexus_established` | Boolean | True / False | Whether a causal link exists between the persecution and the protected ground. This is a critical legal requirement — without it, a claim will fail regardless of risk level. Sampled 70% True. |
| `state_protection_score` | Float | 0.05–1.0 | How capable and willing the home state is to protect the applicant. **Lower = less protection available = stronger refugee claim.** Floored at 0.05 to avoid artifactual exact-zero values. Drawn from Normal(0.3, 0.15). |
| `internal_relocation_possible` | Boolean | True / False | Whether the applicant could safely relocate to another part of their home country. If True, the claim is weaker. Sampled 40% True. |
| `reported_trauma` | Boolean | True / False | Whether the applicant reported trauma during the interview. Higher rates assigned to applicants from high-conflict countries (Syria, Afghanistan, Eritrea, Somalia: ~65% base rate) and those with sexual violence or detention persecution types (+15%). **This variable is intentionally used to penalize credibility — a documented flaw in real systems.** |

---

### Section 3 — System-Generated Scores

| Variable | Type | Range | Formula Summary | Notes |
|----------|------|-------|-----------------|-------|
| `credibility_score` | Float | 0.0–1.0 | Base(Normal 0.65, 0.15) + language effect + education effect + trauma penalty | **Contains intentional bias.** Language and education inflate scores; trauma deflates them. See bias table above. |
| `risk_score` | Float | 0.0–1.0 | Country base risk + persecution type effect + gender effect + noise | Country base rates range from 0.55 (Venezuela) to 0.85 (Syria). Sexual violence adds +0.15; Female +0.08; Non-binary +0.06. |
| `risk_score_uncapped` | Float | Unbounded | Same as `risk_score` before clipping to [0, 1] | Kept for transparency. Students can examine how the hard cap at 1.0 creates an invisible data artifact. |
| `integration_score` | Float | 0.0–1.0 | 0.4 × credibility + 0.2 × age proximity to 35 + 0.4 × random | Represents estimated integration potential if resettled. Note: inherits credibility bias. |

---

### Section 4 — AI Decision Pipeline

| Variable | Type | Values | Notes |
|----------|------|--------|-------|
| `AI_decision` | Categorical | approve, deny | Threshold rule: approve if composite score > 0.62 **AND** credibility > 0.50 **AND** nexus established. Produces ~54% overall approval rate. |
| `human_reviewed` | Boolean | True / False | ~10% of cases flagged for human review. Separate from override — a case can be reviewed without being changed. |
| `human_override` | Boolean | True / False | Among reviewed cases, ~50% result in a flipped decision. Low override rate reflects automation bias in literature. |
| `final_decision` | Categorical | approve, deny | The post-review outcome. Starts as `AI_decision`; flipped where `human_override = True`. **This is the primary outcome variable for analysis.** |
| `processing_time_days` | Integer | ~30–180 | Base: 30–120 days. Human-reviewed cases add 20–60 days. Faster automation does not mean fairer outcomes. |

---

### Section 5 — Outcomes & Audit

| Variable | Type | Values | Notes |
|----------|------|--------|-------|
| `appealed` | Boolean | True / False | ~30% of denied cases go to appeal |
| `appeal_outcome` | Categorical | overturned, upheld, N/A | Among appealed cases: 40% overturned (refugee status granted), 60% upheld (denial confirmed). N/A for non-appealed cases. |
| `bias_flag` | Categorical | none, moderate, severe | Simulates a fairness audit flag. Probability of moderate/severe flag is elevated when: (a) trauma was reported but credibility is low, or (b) nexus was established but case was still denied. Distributions: none ~70%, moderate ~20%, severe ~10% baseline; higher for flagged patterns. |

---

## Approval Rates by Country (Final Decision)

These rates are intentionally varied to reflect both real conflict severity and the way country-of-origin assumptions affect algorithmic outcomes.

| Country | Approximate Approval Rate |
|---------|--------------------------|
| Iraq | ~57% |
| Venezuela | ~58% |
| Syria | ~51% |
| Somalia | ~51% |
| Sudan | ~56% |
| Myanmar | ~46% |
| Eritrea | ~45% |
| Afghanistan | ~50% |

---

## References

Kasapoglu, T., et al. (2021). *Digital geographies of migration governance.* Digital Geography and Society.

Kinchin, I., & Mougouei, D. (2022). *Fairness and transparency in AI-assisted refugee status determination.* International Journal of Refugee Law.

New York State Bar Association. (2022). *Automation and due process in immigration proceedings.*

IRAP. (2023). *Understanding the UNHCR RSD process: A guide for practitioners.*

UNHCR. (1951). *Convention Relating to the Status of Refugees.*
