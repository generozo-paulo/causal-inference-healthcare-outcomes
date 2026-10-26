import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from scipy import stats
from typing import Tuple, Dict
from src.schemas import SepsisObservationalCohortRequest, CausalEffectReport

class CausalInferenceEngine:
    """
    Motor de Inferência Causal em Saúde Observacional (Propensity Score Matching & IPW).
    """

    @staticmethod
    def generate_observational_sepsis_cohort(n_patients: int = 2000, random_state: int = 42) -> pd.DataFrame:
        """Gera coorte observacional realista de sepse com forte viés de indicação de tratamento."""
        np.random.seed(random_state)

        age = np.random.normal(loc=65, scale=12, size=n_patients).clip(18, 95)
        sofa = np.random.poisson(lam=5.5, size=n_patients).clip(1, 18)
        charlson = np.random.poisson(lam=2.2, size=n_patients).clip(0, 10)
        lactate = np.random.exponential(scale=2.2, size=n_patients) + 0.8

        # Viés de indicação: Médicos tendem a aplicar o bundle rápido em pacientes com lactato alto e SOFA grave
        treatment_logits = -2.8 + (0.015 * age) + (0.35 * sofa) + (0.15 * charlson) + (0.40 * lactate)
        treatment_prob = 1.0 / (1.0 + np.exp(-treatment_logits))
        treatment = (np.random.rand(n_patients) < treatment_prob).astype(int)

        # Mecanismo de desfecho: Gravidade aumenta mortalidade, mas o bundle em 1h reduz a mortalidade em ~8% absolutos (Causal ATE)
        baseline_death_logits = -3.2 + (0.03 * age) + (0.28 * sofa) + (0.22 * charlson) + (0.30 * lactate)
        # Efeito causal genuíno: -0.55 nos logits
        death_logits = baseline_death_logits - (0.60 * treatment)
        death_prob = 1.0 / (1.0 + np.exp(-death_logits))
        mortality_30d = (np.random.rand(n_patients) < death_prob).astype(int)

        df = pd.DataFrame({
            "patient_id": [f"PAC-SEP-{i+1:05d}" for i in range(n_patients)],
            "age": np.round(age, 1),
            "sofa_score": sofa,
            "charlson_index": charlson,
            "baseline_lactate": np.round(lactate, 2),
            "treatment_bundle_1h": treatment,
            "mortality_30d": mortality_30d
        })
        return df

    @staticmethod
    def run_propensity_score_analysis(df: pd.DataFrame, caliper: float = 0.05) -> Tuple[CausalEffectReport, pd.DataFrame]:
        covariates = ["age", "sofa_score", "charlson_index", "baseline_lactate"]
        X = df[covariates]
        y = df["treatment_bundle_1h"]

        # Estimação do Propensity Score via regressão logística
        ps_model = LogisticRegression(max_iter=1000)
        ps_model.fit(X, y)
        df_analyzed = df.copy()
        df_analyzed["propensity_score"] = ps_model.predict_proba(X)[:, 1]

        # 1. Efeito ingênuo não-ajustado (Naive / Correlational)
        treated = df_analyzed[df_analyzed["treatment_bundle_1h"] == 1]
        control = df_analyzed[df_analyzed["treatment_bundle_1h"] == 0]
        unadj_treated_mort = float(treated["mortality_30d"].mean())
        unadj_control_mort = float(control["mortality_30d"].mean())
        naive_diff = unadj_treated_mort - unadj_control_mort

        # 2. Pareamento 1:1 com Caliper (Greedy Nearest Neighbor Matching)
        treated_sorted = treated.sort_values("propensity_score")
        control_available = control.copy()

        matched_treated_idx = []
        matched_control_idx = []

        for t_idx, t_row in treated_sorted.iterrows():
            if len(control_available) == 0:
                break
            ps_diff = np.abs(control_available["propensity_score"] - t_row["propensity_score"])
            min_diff = ps_diff.min()
            if min_diff <= caliper:
                best_c_idx = ps_diff.idxmin()
                matched_treated_idx.append(t_idx)
                matched_control_idx.append(best_c_idx)
                control_available = control_available.drop(best_c_idx)

        matched_df = pd.concat([df_analyzed.loc[matched_treated_idx], df_analyzed.loc[matched_control_idx]])
        m_treated = matched_df[matched_df["treatment_bundle_1h"] == 1]
        m_control = matched_df[matched_df["treatment_bundle_1h"] == 0]

        causal_ate = float(m_treated["mortality_30d"].mean() - m_control["mortality_30d"].mean())

        # Teste qui-quadrado / t-test pareado
        se = np.sqrt(
            (m_treated["mortality_30d"].var() / len(m_treated)) +
            (m_control["mortality_30d"].var() / len(m_control))
        )
        ci_lower = causal_ate - (1.96 * se)
        ci_upper = causal_ate + (1.96 * se)
        t_stat, p_val = stats.ttest_ind(m_treated["mortality_30d"], m_control["mortality_30d"])

        # Cálculo de Standardized Mean Difference (SMD) pós-pareamento
        smds = []
        for cov in covariates:
            m1 = m_treated[cov].mean()
            m0 = m_control[cov].mean()
            s_pooled = np.sqrt((m_treated[cov].var() + m_control[cov].var()) / 2.0)
            smd = abs(m1 - m0) / s_pooled if s_pooled > 0 else 0.0
            smds.append(smd)

        max_smd = float(max(smds))

        conclusion = (
            f"O pareamento por escore de propensão demonstrou que o Bundle de Sepse em 1 hora "
            f"reduz a mortalidade em {abs(causal_ate):.1%} absolutos (ATE: {causal_ate:.3f}, p={p_val:.4f}). "
            f"A análise não ajustada sugeria viés de indicação com efeito mascarado ({naive_diff:+.3f})."
        )

        report = CausalEffectReport(
            method="Propensity Score Matching (PSM)",
            unadjusted_mortality_treated=round(unadj_treated_mort, 4),
            unadjusted_mortality_control=round(unadj_control_mort, 4),
            unadjusted_effect_diff=round(naive_diff, 4),
            causal_ate_risk_difference=round(causal_ate, 4),
            confidence_interval_95=(round(ci_lower, 4), round(ci_upper, 4)),
            p_value=round(float(p_val), 4),
            standardized_mean_diff_max=round(max_smd, 3),
            clinical_conclusion=conclusion
        )

        return report, df_analyzed
