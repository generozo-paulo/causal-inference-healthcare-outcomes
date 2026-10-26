# Especificação Contratual (SDD) - Causal Inference on Clinical Outcomes & Sepsis Bundles

## 1. Escopo & Objetivos
Estudo observacional em saúde utilizando **Inferência Causal** para estimar o Efeito Médio do Tratamento (**Average Treatment Effect - ATE**) e Efeito Médio nos Tratados (**ATT**) de um protocolo de intervenção precoce (Bundle de Sepse em 1 hora) sobre a mortalidade em 30 dias.
Corrige o viés de indicação e variáveis de confusão (idade, escore SOFA, comorbidades) através de:
- Escore de Propensão com Pareamento (**Propensity Score Matching - PSM**)
- Ponderação pelo Inverso da Probabilidade de Tratamento (**IPW - Inverse Probability Weighting**)
- Avaliação de Sensibilidade (E-value e Testes de Placebo)

## 2. Contratos de Entrada (Pydantic)

### 2.1 Coorte Observacional de Sepse (`SepsisObservationalCohortRequest`)
- `n_patients`: int = Field(default=2000, ge=200)
- `propensity_caliper`: float = Field(default=0.05, gt=0.0, lt=0.5)
- `confounders_list`: List[str] = ["age", "sofa_score", "charlson_index", "baseline_lactate"]

## 3. Contratos de Saída (Pydantic)

### 3.1 Relatório de Inferência Causal (`CausalEffectReport`)
- `method`: Literal["Propensity Score Matching (PSM)", "Inverse Probability Weighting (IPW)"]
- `unadjusted_effect_diff`: float
- `causal_ate_risk_difference`: float
- `confidence_interval_95`: Tuple[float, float]
- `p_value`: float
- `standardized_mean_diff_max`: float # Balanço de covariáveis (< 0.1 indica pareamento ideal)
- `clinical_conclusion`: str
