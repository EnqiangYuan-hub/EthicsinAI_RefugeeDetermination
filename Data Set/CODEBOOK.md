# Refugee Status Determination Simulation — Codebook

The synthetic dataset models how an automated decision-making system could process refugee status applications by transforming individual traits and legal information into numerical scores, then applying threshold-based classification and limited human oversight.

To be recognized as a refugee under the [1951 Refugee Convention](https://www.unhcr.org/en-us/1951-refugee-convention.html), an applicant must demonstrate a well-founded fear of persecution based on one of five protected grounds (race, religion, nationality, political opinion, or membership in a particular social group), that their home country cannot or will not protect them, and that internal relocation is not a safe option. This dataset simulates an AI system evaluating those criteria.

---

## Overall Flow

```
Applicant Data (demographics + legal claim)
            ↓
┌───────────────────────────────────────┐
│           Scoring Functions           │
│  credibility_score  (language, edu,   │
│                      trauma penalty)  │
│  risk_score         (country, gender, │
│                      persecution)     │
│  integration_score  (credibility, age)│
│                                       │
└───────────────────────────────────────┘
            ↓
    Composite Score S
            ↓
    AI Decision 
            ↓
    Human Review
            ↓  
    Final Decision
            ↓
    If Denied → Appeal (30% file) → overturned (40%) / upheld (60%)
            ↓
    Bias Audit → bias_flag (none / moderate / severe)
```

---

## Variable Reference

### Applicant Inputs

| Variable | Type / Range | Determination Logic |
|----------|-------------|---------------------|
| `id` | Integer (1–500) | Sequential identifier |
| `country_of_origin` | Categorical (8 values) | Uniform random draw from: Syria, Afghanistan, Sudan, Myanmar, Eritrea, Venezuela, Iraq, Somalia |
| `gender` | Categorical | Random draw with probabilities [0.48, 0.48, 0.04] for Male, Female, Non-binary. Proportions reflect real RSD caseload demographics; ~4% Non-binary surfaces underrepresentation in algorithmic audits |
| `age` | Integer (18–64) | Uniform random draw |
| `education_level` | Ordinal | Random draw from None, Primary, Secondary, Tertiary with probabilities [0.10, 0.30, 0.40, 0.20] |
| `language_proficiency` | Ordinal | Random draw from None, Basic, Intermediate, Advanced, Fluent with probabilities [0.05, 0.25, 0.40, 0.20, 0.10] |
| `family_size` | Integer (1–6) | Uniform random draw |
| `prior_camp_years` | Integer (0–9) | Uniform random draw representing years spent in a refugee camp before this application |
| `persecution_ground` | Categorical | Uniform random draw from the five 1951 Convention grounds: race, religion, nationality, political_opinion, social_group |
| `persecution_type` | Categorical | Uniform random draw from: violence, detention, threats, sexual_violence, discrimination |
| `nexus_established` | Boolean | Random draw with P(True) = 0.70. Represents whether a causal link exists between the persecution and a protected ground — a critical legal requirement without which a claim fails regardless of risk level |
| `state_protection_score` | Continuous [0.05–1.0] | Normal(0.3, 0.15), clipped with a floor of 0.05. Represents the home state's capacity and willingness to protect the applicant. Lower score = weaker state protection = stronger refugee claim |
| `internal_relocation_possible` | Boolean | Random draw with P(True) = 0.40. If True, the applicant could safely relocate within their home country, weakening the claim |
| `reported_trauma` | Boolean | Bernoulli draw with base rate ~65% for high-conflict countries (Syria, Afghanistan, Eritrea, Somalia) and cases involving sexual violence or detention; ~40% otherwise. **Intentionally used to penalize credibility — a documented flaw in real systems** |

---

## Feature Computation

Three continuous scores are derived from applicant inputs to simulate AI-driven assessment:

**Credibility Score**

$$C = \text{Base} \sim \mathcal{N}(0.65,\ 0.15) + L_{\text{effect}} + E_{\text{effect}} + T_{\text{penalty}}$$

Language effect: None = −0.20, Basic = −0.10, Intermediate = 0, Advanced = +0.05, Fluent = +0.10  
Education effect: None = −0.10, Primary = 0, Secondary = +0.05, Tertiary = +0.10  
Trauma penalty: −0.08 if `reported_trauma = True`. Final score clipped to [0, 1]  

**Risk Score**

$$R = \text{Country base} + G_{\text{effect}} + P_{\text{effect}} + \varepsilon, \quad \varepsilon \sim \mathcal{N}(0,\ 0.05)$$

Country base rates range from 0.55 (Venezuela) to 0.85 (Syria)   
Gender effect: Male = 0, Female = +0.08, Non-binary = +0.06   
Persecution type effect: sexual\_violence = +0.15, violence = +0.10, detention = +0.05, threats = 0, discrimination = −0.05  
Risk score is clipped to [0, 1]; raw pre-clip value retained as `risk_score_uncapped`  

**Integration Score**

$$I = 0.4C + 0.2\left(1 - \frac{|age - 35|}{35}\right) + 0.4\varepsilon$$

Measures predicted adaptability if resettled to new country
Credibility (40%) — inherits language, education, and trauma bias from credibility_score
Age proximity to 35 (20%) — peaks at age 35, decreases in both directions
Random noise (40%) — represents unpredictable external factors (host community, job market, etc.)

### Calculated Scores

| Variable | Type / Range | Determination Logic |
|----------|-------------|---------------------|
| `credibility_score` | Continuous [0–1] | See formula above. Contains intentional bias: language and education inflate scores; trauma deflates them |
| `risk_score` | Continuous [0–1] | See formula above. Clipped at 1.0 |
| `risk_score_uncapped` | Continuous (unbounded) | Raw pre-clip value retained so students can examine the artifact introduced by the hard cap at 1.0 |
| `integration_score` | Continuous [0–1] | See formula above. Inherits credibility bias through the C term |

---

### System Process

## AI Decision Rule

S = 0.45 * R + 0.30 * C + 0.15 * `nexus_established` + 0.10 * (1 - 'state_protection_score')

AI_decision = "approve"  if S > 0.62 AND C > 0.50 AND nexus_established = True
            = "deny"      otherwise
 

| Variable | Type / Range | Determination Logic |
|----------|-------------|---------------------|
| `AI_decision` | Categorical (approve / deny) | See decision rule above |
| `human_reviewed` | Boolean | ~10% of cases randomly flagged for human review. Separate from override — a case can be reviewed without the decision being changed |
| `human_override` | Boolean | Among reviewed cases, ~50% result in a flipped decision. |
| `final_decision` | Categorical (approve / deny) | Starts as `AI_decision`; flipped where `human_override = True`. **Primary outcome variable for analysis** |
| `processing_time_days` | Integer (~30–180) | Base time Uniform(30, 120). Human-reviewed cases add Uniform(20, 60) days, representing the trade-off between oversight and efficiency |

### Outcomes

| Variable | Type / Range | Determination Logic |
|----------|-------------|---------------------|
| `appealed` | Boolean | For denied cases: 30% randomly assigned True |
| `appeal_outcome` | Categorical (overturned / upheld / N/A) | If appealed: 40% overturned (refugee status granted), 60% upheld (denial confirmed). N/A for non-appealed cases |
| `bias_flag` | Categorical (none / moderate / severe) | Simulates a fairness audit. Probability of moderate/severe elevated when trauma was reported but credibility is low, or when nexus was established but the case was still denied. Baseline: none ~70%, moderate ~20%, severe ~10% |

---

## References

Kasapoglu, T., et al. (2021). Digital geographies of migration governance. *Digital Geography and Society.*

Kinchin, I., & Mougouei, D. (2022). Fairness and transparency in AI-assisted refugee status determination. *International Journal of Refugee Law.*

New York State Bar Association. (2022). *Automation and due process in immigration proceedings.*

IRAP. (2023). *Understanding the UNHCR RSD process: A guide for practitioners.*

UNHCR. (1951). *Convention Relating to the Status of Refugees.*
