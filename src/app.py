import streamlit as st
import pandas as pd
import plotly.express as px
from src.schemas import SepsisObservationalCohortRequest
from src.causal_engine import CausalInferenceEngine

st.set_page_config(
    page_title="Causal Inference on Healthcare Outcomes",
    page_icon="⚖️",
    layout="wide"
)

st.title("⚖️ Causal Inference on Clinical Outcomes (Sepsis Care)")
st.markdown("""
Estudo observacional em saúde aplicando **Inferência Causal** com **Propensity Score Matching (PSM)** para corrigir o **Viés de Indicação** e mensurar o impacto real do Bundle de Sepse em 1 hora sobre a mortalidade hospitalar.
""")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("⚙️ Configurações da Coorte Observacional")
    n_patients = st.slider("Tamanho da Coorte de Pacientes", 1000, 4000, 2000, 500)
    caliper = st.slider("Caliper de Tolerância de Pareamento", 0.01, 0.10, 0.05, 0.01)

    df_cohort = CausalInferenceEngine.generate_observational_sepsis_cohort(n_patients=n_patients)
    report, df_analyzed = CausalInferenceEngine.run_propensity_score_analysis(df_cohort, caliper=caliper)

    st.markdown("### 📊 Contraste: Correlação vs. Causalidade")
    st.metric("Efeito Ingênuo Não-Ajustado (Naive Δ)", f"{report.unadjusted_effect_diff:+.1%}")
    st.metric("Efeito Causal Genuíno (ATE)", f"{report.causal_ate_risk_difference:.1%}", delta=f"{report.causal_ate_risk_difference:.1%}")
    st.metric("p-valor do Efeito Causal", f"{report.p_value:.4f}")
    st.metric("Balanço de Covariáveis (Max SMD)", f"{report.standardized_mean_diff_max:.3f}", help="Ideal se menor que 0.10")

with col2:
    st.subheader("Diagnóstico de Sobreposição do Escore de Propensão (Common Support)")
    fig_ps = px.histogram(
        df_analyzed,
        x="propensity_score",
        color="treatment_bundle_1h",
        barmode="overlay",
        title="Distribuição do Propensity Score (Grupo Tratado vs. Controle)",
        labels={"propensity_score": "Escore de Propensão P(Tratamento | X)", "treatment_bundle_1h": "Bundle Sepse 1h (1=Sim, 0=Não)"},
        color_discrete_map={0: "#1f77b4", 1: "#ff7f0e"}
    )
    st.plotly_chart(fig_ps, use_container_width=True)

    st.markdown("### 🩺 Conclusão Clínica & Epidemiológica")
    st.success(report.clinical_conclusion)

    st.markdown("### Intervalo de Confiança 95% do ATE")
    st.info(f"IC 95%: `[{report.confidence_interval_95[0]:.2%}, {report.confidence_interval_95[1]:.2%}]`")
