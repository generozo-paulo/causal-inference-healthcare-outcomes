from pydantic import BaseModel, Field
from typing import List, Tuple, Literal

class SepsisObservationalCohortRequest(BaseModel):
    n_patients: int = Field(default=2000, ge=200)
    propensity_caliper: float = Field(default=0.05, gt=0.0, lt=0.5)

class CausalEffectReport(BaseModel):
    method: Literal["Propensity Score Matching (PSM)", "Inverse Probability Weighting (IPW)"]
    unadjusted_mortality_treated: float
    unadjusted_mortality_control: float
    unadjusted_effect_diff: float
    causal_ate_risk_difference: float
    confidence_interval_95: Tuple[float, float]
    p_value: float
    standardized_mean_diff_max: float
    clinical_conclusion: str
