# Respostas Finais — Pesquisa de Mercado NOVO CR

> Síntese consolidada dos três blocos de pesquisa. Detalhes e fontes completas em:
> [`01_alunos_rio_e_fgv.md`](./01_alunos_rio_e_fgv.md) · [`02_concorrentes.md`](./02_concorrentes.md) · [`03_custos_infra_e_equipe.md`](./03_custos_infra_e_equipe.md)
>
> Flag de confiança: 🟢 dado oficial/de fonte · 🟡 estimativa. Pesquisa realizada jun/2026.

---

## Tabela-resumo (uma linha por pergunta)

| # | Pergunta | Resposta-chave | Ano | Flag |
|---|---|---|---|---|
| **1** | Alunos na rede municipal do Rio | **~650.000** em 1.557 escolas (maior rede municipal da América Latina) | 2026 | 🟢 |
| **1.1** | GECs/GETs especificamente | **~11.000** (núcleo experimental) até **~30.000** (com expansão de tempo integral) | 2023 | 🟢/🟡 |
| **1.2** | Municipais "normais" | **~620.000–640.000** (total − GEC/GET) | 2026 | 🟡 |
| **1.3** | Escolas federais (Rio) | **~40.000–50.000** (CPII 12k + IFRJ ~20k + CEFET ~15k) | 2023–24 | 🟡 |
| **1.4** | Grupo que controla pH/Pensi (Grupo Salta, ex-Eleva) | **>117.000 alunos**, >170 unidades, 22 escolas próprias, R$ 2,1 bi receita | 2023–24 | 🟢 |
| **1.4.1** | Split Rio vs fora | **~55 unidades no RJ** (Pensi 21 + pH 12 + Elite 22); restante (~115+) fora, em 16 estados + DF | 2023 | 🟡 |
| **1.5** | Rede estadual (SEEDUC) | **~600.000–750.000** no estado, >1.200 escolas (opera o Ensino Médio) | 2023–24 | 🟡 |
| **1.6** | FGV | **>5.000 graduação** + **101.057 educação continuada**; >100 cursos | recente | 🟢 |
| **2** | Quem faz "igual" ao NOVO CR | **NÃO é a Descomplica.** Diretos: **Letrus, Cria** (BR); **Gradescope, EssayGrader, CoGrader** (global) | 2024–26 | 🟢 |
| **2.2** | Market share | Sem consolidado público; Letrus/Cria lideram BR; Gradescope/EssayGrader global. Mercado AES ~US$123–430 mi, CAGR ~12% | 2024–26 | 🟢/🟡 |
| **2.3** | Valor de mercado | Descomplica >US$100 mi captados; **Turnitin vendida ~US$1,75 bi** (proxy da categoria); startups de correção sem valuation público | 2019–24 | 🟢/🟡 |
| **3.1** | GPU para modelos locais | 7–8B: **~R$ 2.400** (RTX 3060); 30B+: **~R$ 5–19 mil** (RTX 3090); 70B: **~R$ 40–48 mil** | 2026 | 🟢 |
| **3.2** | Designer/mês | Júnior ~R$ 3.000–3.500 · **Pleno ~R$ 5.500–6.000** · Sênior ~R$ 9.000–12.000 | 2026 | 🟢 |
| **3.3** | Backend dev/mês | Júnior ~R$ 3.400–4.500 · **Pleno ~R$ 7.800** · Sênior ~R$ 12.400–20.900 | 2026 | 🟢 |

---

## Bloco 1 — Dimensão do mercado (alunos)

- A **rede municipal do Rio** (~650 mil alunos) é o maior alvo único, mas é majoritariamente **Educação Infantil + Fundamental** (não tem Ensino Médio regular).
- Os **GECs/GETs** são um nicho pequeno (~11–30 mil) mas de alto perfil — modelo inovador/tempo integral, bom para piloto-vitrine.
- **Ensino Médio** (onde correção de provas/redação é mais intensa) está na **rede estadual SEEDUC** (~600–750 mil no estado) e nas **federais** (~40–50 mil, alto desempenho/prestígio: CPII, IFRJ, CEFET).
- O **Grupo Salta (ex-Eleva)** é o maior alvo **privado** (>117 mil alunos), com ~55 unidades concentradas no RJ (pH, Pensi, Elite) — decisor de compra centralizado, atrativo para venda B2B.
- A **FGV** tem graduação enxuta (~5 mil) mas marca forte; o grosso (101 mil) é educação continuada/executiva, menos aderente a correção de provas no formato do NOVO CR.

**TAM aproximado (alunos potencialmente endereçáveis no Rio/RJ):** somando municipal + estadual + federal + Salta-RJ ≈ **1,3–1,5 milhão de alunos** na grande RJ (🟡 estimativa de ordem de grandeza). O **SAM** realista de curto prazo concentra-se em **Ensino Médio + privado (Salta) + federais**, onde a dor de correção é maior.

## Bloco 2 — Concorrência

- **Correção "igual" ao NOVO CR é categoria nascente e fragmentada**, sem dominante no Brasil → **janela de entrada**.
- **Concorrentes diretos a vigiar:** **Letrus** (líder em rede pública, escala estadual + SESI) e **Cria** (240 mil alunos, foco ENEM). Globais: **Gradescope/Turnitin** (universidades) e **EssayGrader** (professores em escala).
- **Maioria é especializada só em redação** ou só em manuscrito/múltipla escolha. O **diferencial do NOVO CR** = correção **genérica, multi-questão, multi-provider (OpenAI/Anthropic/Google), pipeline transparente em PT-BR**.
- **Descomplica é adjacente**, não concorrente direto: é cursinho/faculdade digital. Disputa orçamento, não o mesmo job-to-be-done.
- **Tamanho de mercado:** AES ~US$123–430 mi hoje → ~US$1+ bi na próxima década (CAGR ~12%); IA-educação guarda-chuva ~US$2,2 bi → US$5,8 bi até 2030 (CAGR ~17,5%).

## Bloco 3 — Custos (BRL)

- **Rodar modelos locais** só compensa para 7B–34B: melhor custo-benefício é **RTX 3090 24GB (~R$ 5–19 mil)**. Para 70B (~R$ 40–48 mil + energia), **APIs/nuvem geralmente vencem** hoje — local só por privacidade ou volume altíssimo constante.
- **Equipe mínima:** designer pleno (~R$ 5,5–6 mil) + backend pleno (~R$ 7,8 mil) ≈ **R$ 13–14 mil/mês** (base, sem encargos CLT, que somam ~70–100%).

---

## Implicações estratégicas para o NOVO CR

1. **Foco de mercado:** priorizar onde a **dor de correção é maior** — Ensino Médio (estadual/federal) e o **privado consolidado (Grupo Salta)**, que tem decisor B2B centralizado e >117 mil alunos. A rede municipal é grande mas pouco aderente (sem Ensino Médio).
2. **Posicionamento vs concorrentes:** vender o que Letrus/Cria **não** fazem — correção **genérica multi-questão** (não só redação) + **multi-provider** + **transparência do pipeline**. Em PT-BR, com contexto ENEM/vestibular.
3. **Mercado em formação:** sem líder consolidado no BR e mercado crescendo ~12–17% a.a. → momento de capturar share. Turnitin (~US$1,75 bi) prova que a categoria tem valor de saída relevante.
4. **Custo de operar é baixo:** ~R$ 13–14 mil/mês de equipe-núcleo + custo de API (ou ~R$ 5–19 mil one-off de GPU se for local). Viável para bootstrap/MVP antes de captar.

---

## Lacunas e ressalvas (o que confirmar antes de decisões grandes)

- **1.3 / 1.5:** números de IFRJ, CEFET e total exato da rede estadual são **estimativas** — confirmar no Censo Escolar INEP 2024 e em "Seeduc em Números".
- **1.4.1:** split de **alunos** (não unidades) Rio vs fora do Grupo Salta não é público — exigiria relatório de RI.
- **2.2 / 2.3:** market share e valuations de Letrus/Cria/EssayGrader **não são públicos** — estimativas por proxies (alunos, unidades, aquisição da Turnitin).
- **3.1:** preços de GPU oscilam fortemente; faixas refletem varejo BR de jun/2026.
