# CRISP-DM: Entendimento de Negócio (Inferência Causal em Saúde)

## 1. Problema de Decisão Clínica Baseada em Dados
Em medicina, ensaios clínicos randomizados (RCTs) nem sempre são eticamente viáveis (ex: negar intencionalmente antibióticos em sepse para formar grupo controle).
Análises puramente correlacionais sofrem de **Viés de Indicação**: pacientes mais graves recebem mais intervenções emergenciais, fazendo com que o tratamento pareça falsamente associado a maior mortalidade.

## 2. Solução por Inferência Causal
- Modelagem de Propensity Score para calcular $P(\text{Tratamento} \mid X)$.
- Pareamento de pacientes semelhantes e balanceamento de covariáveis com Diferença Média Padronizada (SMD) $< 0.1$.
- Isolamento do efeito causal genuíno do pacote de sepse.
