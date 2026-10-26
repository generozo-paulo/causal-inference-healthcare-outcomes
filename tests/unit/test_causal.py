import pytest
from src.causal_engine import CausalInferenceEngine

def test_sepsis_cohort_generation():
    df = CausalInferenceEngine.generate_observational_sepsis_cohort(n_patients=500)
    assert len(df) == 500
    assert "treatment_bundle_1h" in df.columns
    assert "mortality_30d" in df.columns
    assert "sofa_score" in df.columns

def test_causal_effect_estimation():
    df = CausalInferenceEngine.generate_observational_sepsis_cohort(n_patients=1500)
    # Com caliper mais estrito (0.04) o pareamento reduz as discrepâncias
    report, df_analyzed = CausalInferenceEngine.run_propensity_score_analysis(df, caliper=0.03)
    assert "propensity_score" in df_analyzed.columns
    # O bundle deve reduzir a mortalidade causalmente (ATE negativo)
    assert report.causal_ate_risk_difference < 0.0
    assert report.standardized_mean_diff_max < 0.30
    assert len(report.confidence_interval_95) == 2
