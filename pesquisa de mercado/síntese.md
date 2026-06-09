# Síntese — Pesquisa de Mercado NOVO CR (documento vivo)

> Documento conjunto Otavio + Claude, montado em conversa. Objetivo: ter os números **na ponta da língua** e estimar **ganhos futuros**.
> Última atualização: jun/2026. Flags: 🟢 dado de fonte · 🟡 estimativa.

---

## A "cola" — números para decorar

**Mercado (alunos, Rio):**
- Municipal: **~650 mil** (mas é Infantil+Fundamental — sem Ensino Médio)
- GEC/GET: **~11–30 mil** (nicho-vitrine, tempo integral)
- Estadual (SEEDUC): **~600–750 mil** no estado — *aqui está o Ensino Médio*
- Federais: **~40–50 mil** (Pedro II 12k, IFRJ ~20k, CEFET ~15k)
- Grupo Salta (pH/Pensi/Elite): **>117 mil alunos**, ~55 unidades no RJ, R$ 2,1 bi de receita
- FGV: **~5 mil** graduação + 101 mil educação executiva

**Concorrência (uma frase):** *"Quem corrige por IA no Brasil hoje corrige só redação (Letrus, Cria). Quem corrige prova inteira (Gradescope) é gringo, inglês-first e universitário. Ninguém faz prova completa, multi-questão, em português."*

**Preços de referência da categoria — as 4 lógicas do mercado (detalhe em `02_concorrentes.md`):**

| Lógica de preço | Exemplos | Valor |
|---|---|---|
| **Por correção** (BR redação) | Imaginie R$ 7–9,90/redação; Redação Online R$ 17–38 (humana) | **R$ 5–10/correção IA** |
| **Por aluno/ano** (global institucional) | Turnitin US$ 1,79–6,50; Gradescope ~US$ 4/aluno/curso (UGA) | **~R$ 10–35/aluno/ano** |
| **Por professor/mês** | EssayGrader US$ 6,99–14,99; CoGrader US$ 19; MagicSchool US$ 11,99 | **~R$ 37–100/mês** |
| **Por escola/ano** | MagicSchool District US$ 3.999/escola | **~R$ 21 mil/escola/ano** |

- **Letrus:** preço não público; entra **de graça** (MS, 48 mil alunos) e depois vira política pública paga. 🟢
- **Insight central:** o mercado BR paga **R$ 5–10 por correção de IA** de redação — e o custo real com LLM é **centavos** (~R$ 0,15–0,50/prova, ver seção de custo). Quem define a lógica de cobrança certa para prova completa multi-questão captura essa diferença.

---

## Estimativa de ganhos futuros (cenários)

> Premissa de preço: **R$ 20/aluno/ano** (meio da faixa Turnitin/Gradescope convertida) no B2B institucional,
> ou **R$ 120/professor/mês** no modelo por professor. Ajustar conforme posicionamento.

### Cenário 1 — "Pé na porta" (ano 1): privado + nicho
| Cliente | Alunos | Receita/ano (R$20/aluno) |
|---|---|---|
| 2–3 escolas privadas médias (~1.500 alunos cada) | ~4.000 | **R$ 80 mil** |
| 1 federal piloto (ex.: 1 campus Pedro II) | ~1.000 | R$ 20 mil |
| **Total ano 1** | ~5.000 | **~R$ 100 mil ARR** 🟡 |

### Cenário 2 — "Tração" (ano 2-3): um contrato-âncora
| Cliente | Alunos | Receita/ano |
|---|---|---|
| Grupo Salta — só marcas RJ (pH/Pensi/Elite) | ~50.000 🟡 | **R$ 1,0 mi** |
| 10 escolas privadas avulsas | ~15.000 | R$ 300 mil |
| Federais (CPII completo) | ~12.000 | R$ 240 mil |
| **Total** | ~77.000 | **~R$ 1,5 mi ARR** 🟡 |

### Cenário 3 — "Escala" (ano 3-5): entra o setor público
| Cliente | Alunos | Receita/ano |
|---|---|---|
| SEEDUC-RJ (rede estadual, via licitação) | ~600.000 | **R$ 12 mi** (a R$20/aluno) |
| Base privada acumulada | ~100.000 | R$ 2 mi |
| **Total** | ~700.000 | **~R$ 14 mi ARR** 🟡 |

**Sanity check com players reais:** a Letrus, líder da categoria no BR, atingiu ~450 mil alunos impactados em ~8 anos — ou seja, o Cenário 3 (~700 mil) é teto agressivo de 5 anos, não base. Um cenário-base honesto para 3 anos é **R$ 0,5–1,5 mi ARR**; o público (Cenário 3) é o bilhete de loteria que depende de licitação.

**Modelo alternativo (por professor):** 500 professores pagantes × R$120/mês = **R$ 720 mil/ano** — mais rápido de testar (self-service), churn maior. CoGrader e EssayGrader provam que professores pagam do próprio bolso.

### Custo por prova (token economics) — o número que prova a margem

> Premissas de UMA prova (multi-questão, ~3–5 páginas escaneadas, pipeline de 6 estágios do NOVO CR):
> **~40.000 tokens de input** (prompts + imagens de visão + re-feed de contexto entre estágios) e
> **~10.000 tokens de output** (JSONs estruturados somados). Câmbio usado: **~R$ 5,30/US$**. 🟡

| Modelo | US$/1M (in/out) | Custo/prova (US$) | Custo/prova (BRL) |
|---|---|---|---|
| **gpt-5-mini** | 0,25 / 2,00 | $0,030 | **~R$ 0,16** |
| **Gemini 3 Flash** | 0,50 / 3,00 | $0,050 | **~R$ 0,27** |
| **Haiku 4.5** | 1,00 / 5,00 | $0,090 | **~R$ 0,48** |
| **Sonnet 4.6** (premium) | 3,00 / 15,00 | $0,270 | **~R$ 1,43** |

- Com **prompt caching** (os prompts de sistema repetem a cada prova), o custo de input cai ~50–90% → operação real com modelo barato fica em **~R$ 0,15–0,30/prova**. 🟡
- **Custo de API por aluno/ano:** se cada aluno tem ~8–12 provas corrigidas/ano → **~R$ 1,50–5,00/aluno/ano** (modelo barato).

### Margem (software-like)

A R$ 20/aluno/ano de preço e ~R$ 1,5–5 de custo de API → **margem bruta de ~75–90%**.
O custo de IA **não é o gargalo** — o gargalo é venda (contrato-âncora) e folha de equipe.

| Item | Valor | Flag |
|---|---|---|
| Custo de IA por aluno/ano | R$ 1,50–5,00 | 🟡 |
| Preço por aluno/ano (base) | R$ 20 (faixa R$ 20–40) | 🟡 |
| **Margem bruta** | **~75–90%** | 🟡 |
| Equipe-núcleo (designer + backend pleno) | R$ 13–14 mil/mês base; **~R$ 24 mil/mês carregado CLT** (encargos ~80%) ou ~R$ 16–20 mil PJ | 🟢 |
| **Breakeven** | **~R$ 300–500 mil ARR** paga a operação enxuta | 🟡 |

---

## Plano de 1 ano (curto prazo) — tese FGV → Pensi

> Premissa do Otavio: round FGV fecha em **novembro/2026** (Mário/CTAE) → montar time →
> primeiro cliente = **controladoria do Pensi (Grupo Salta)** via sócio → **ROI em ~6 meses**.

### Linha do tempo

| Período | Fase | O que acontece |
|---|---|---|
| **Jun–Out/2026** | Pré-venda + produto | Bootstrap (founder). Conversas com Pensi/Salta via sócio; refinar produto e demo. |
| **Nov/2026** | 💰 Round FGV fecha | Capital entra. Contratar time. |
| **Nov–Dez/2026** | Montar time + 1ª venda | 1 backend pleno + 1 designer pleno. Fechar **piloto pago com Pensi**. |
| **Q1/2027** | Faturamento | Primeiro contrato rodando. ROI dentro de ~6 meses do aporte. |

### Custos mensais após o aporte (regime CLT carregado)

| Item | R$/mês |
|---|---|
| Backend pleno (carregado ~80%) | ~14.000 |
| Designer pleno (carregado ~80%) | ~10.000 |
| Pró-labore founder | ~10.000 |
| API/infra (baixo no início) | ~1.000–3.000 |
| Contador, ferramentas, nuvem | ~2.000–3.000 |
| **Burn total** | **~R$ 37.000–40.000/mês** (PJ: ~R$ 28–32 mil) |

- **Runway de 12 meses** ≈ **R$ 450–480 mil** → **sugestão de round: ~R$ 500 mil** (12 meses + folga). 🟡
- **6 meses de runway** (Nov–Abr) ≈ **R$ 220–240 mil**.

### Primeira venda (piloto Pensi) e ROI

| Cenário de piloto | Alunos | Receita/ano (R$ 20/aluno) |
|---|---|---|
| Piloto pequeno (1 marca/subconjunto) | 5.000 | **R$ 100 mil** |
| Piloto médio (pH **ou** Pensi parcial) | 10.000 | **R$ 200 mil** |
| Marcas RJ inteiras (pH+Pensi+Elite) | ~50.000 | **R$ 1,0 mi** |

- Um **piloto de R$ 100–200 mil ARR** fechado em ~6 meses cobre o burn do mesmo período → **ROI ~6 meses**, batendo a tese. ✅
- Se subir o ticket para **R$ 30–40/aluno** (defensável: Turnitin cobra US$2–6 = R$ 10–32, e Pensi é premium), o mesmo piloto vira **R$ 150–400 mil ARR**.

### Sensibilidade do preço (piloto de 10.000 alunos)

| Preço/aluno/ano | ARR do piloto |
|---|---|
| R$ 15 | R$ 150 mil |
| R$ 20 (base) | R$ 200 mil |
| R$ 30 | R$ 300 mil |
| R$ 40 | R$ 400 mil |

---

## Bloco 1 — Alunos: leitura estratégica (quem é endereçável de verdade)

> O número bruto engana. O que importa para o NOVO CR é **onde a dor de correção é maior** (provas longas/discursivas/vestibular) e **quão fácil é vender** (decisor central vs licitação).

**A nuance-chave:** o maior pool único — **rede municipal do Rio (650 mil)** — é **Educação Infantil + Fundamental** (não tem Ensino Médio regular). Provas existem (Fundamental II), mas são mais simples. **A dor de correção pesada (prova longa, discursiva, vestibular/ENEM) está no Ensino Médio** → que está na **rede estadual, federal e privada**, não na municipal.

### Ranking de endereçabilidade (beachheads)

| Tier | Pool | Alunos | Por que / dificuldade de venda |
|---|---|---|---|
| **1** | **Grupo Salta** (pH/Pensi/Elite) | 117 mil (~50k RJ) | Privado, **sócio dá acesso**, decisor central. Ensino médio + vestibular = dor máxima. **Melhor beachhead.** |
| **1** | **FGV** | 9 mil | Privado, prestígio, marca de pitch. Processo mais lento, mas alto valor. |
| **2** | **Federais RJ** (CPII ~12k + **IFRJ 18k** + CEFET ~15k) | ~45 mil | Provas sérias, prestígio (vira case). Compra federal é burocrática. |
| **2** ⬆️ | **Municipal Rio** (✅ subido pelo Otavio) | 650 mil | Infantil+Fundamental (dor menor por aluno, mas **volume enorme de provas**). **Otavio tem contatos na Prefeitura.** Porta de entrada = **piloto GEC/GET** (11–30k) → licitação municipal. |
| **3** | **Estadual SEEDUC** | 600–750 mil (estado) | **Aqui está o Ensino Médio** (6,5 mi no BR). Dor máxima + escala, mas **licitação lenta**. |

**Leitura (ajustada pelo Otavio):** sequência = **privado primeiro (Salta/FGV)** pela dor alta + venda rápida; **município do Rio subiu** porque o Otavio tem acesso à Prefeitura e o volume de provas é gigante (mesmo no fundamental), com o piloto GEC/GET como porta de entrada → licitação; **estadual depois** pela escala mas com licitação mais lenta. O número bruto (650 mil municipal) deixa de ser só "grande mas inacessível" e vira **alvo de Tier 2 por causa do relacionamento.**

---

## Bloco 3 — Custos: GPU local vs API + equipe

### A decisão central: rodar modelo local (GPU) ou usar API?

**Preço das GPUs para rodar open-source local (em BRL):**

| Modelo open-source | VRAM | GPU | Preço (one-off) |
|---|---|---|---|
| 7–8B (Llama 3 8B, Mistral) | ~6 GB | RTX 3060 12GB | ~R$ 2.400 |
| 30–34B | ~24 GB | **RTX 3090 24GB** | ~R$ 5.000–19.000 |
| 70B (qualidade frontier-ish) | ~42 GB | 2× RTX 4090 ou **A6000 48GB** | ~R$ 40.000–48.000 |
| **405B / 671B (nível Opus, fronteira)** | **~640 GB–1 TB** (FP8) | **8× NVIDIA H100 80GB** (servidor DGX-class) | **~R$ 1,1–1,7 milhões** |
| **671B full / topo Blackwell** | ~700 GB–1,4 TB | **4× B200** (DeepSeek 671B FP8) → **DGX B200 (8×)** → **rack GB200 NVL72 (72 GPUs)** | **R$ 0,6–1,1 mi → R$ 2,7 mi → ~R$ 16 mi** |

**Teto absoluto do mercado (geração Blackwell, 2026):**
- **B200** (SXM, 180–192 GB): US$ 30–50 mil/placa. **GB200 Superchip:** US$ 60–70 mil.
- **4× B200** rodam o **DeepSeek 671B** completo em FP8 (720 GB) → ~**R$ 0,6–1,1 milhão**.
- **DGX B200** (8× B200, 1,44 TB): **US$ 515 mil ≈ R$ 2,7 milhões**.
- **Rack GB200 NVL72** (72 GPUs — o topo, para treinar/servir em escala): **~US$ 3 milhões ≈ R$ 16 milhões**.
- Aluguel nuvem: B200 ~US$ 2,25–16/GPU/h; GB200 ~US$ 10–20/GPU/h.

**Para rodar um modelo nível Opus localmente (a pergunta do Otavio):**
- **Llama 3.1 405B** (maior Llama 3) precisa de ~810 GB em FP16 / ~640 GB em FP8 → roda num nó de **8× H100 (640 GB)**. DeepSeek 671B precisa ainda mais.
- **Custo do hardware:** H100 80GB = **US$ 25–40 mil/placa**; servidor **8× H100 = US$ 200–320 mil ≈ R$ 1,1–1,7 milhões** (one-off). + **luz ~R$ 78 mil/ano** (rig ~10 kW, 24/7) + refrigeração + ops.
- **Alternativa nuvem:** alugar 8× H100 a ~US$ 2,7–10/GPU/h → **~R$ 80–230 mil/MÊS** rodando 24/7.

**Crossover do nível Opus:**
- 8× H100 (R$ 1,4 mi) amortizado em 3 anos + luz = **~R$ 550 mil/ano fixo**. Vs API de qualidade Opus/Sonnet (~R$ 1,43/prova) → break-even em **~385 mil provas/ano (~38 mil alunos)**.

> **Mas o ponto-chave:** **corrigir prova NÃO precisa de modelo nível Opus.** Os modelos baratos (gpt-5-mini, Gemini Flash, Haiku) já fazem a correção bem a R$ 0,15–0,50/prova. Comprar 8× H100 para corrigir prova é **Ferrari para entregar pizza** — overkill que só se paga em escala gigante (~40 mil+ alunos) E se a qualidade de fronteira fosse realmente necessária (não é). **Recomendação: nem considerar hardware de fronteira;** se um dia quiser qualidade Opus, é mais barato chamar a API do Opus/Sonnet do que amortizar R$ 1,5 mi de GPU.

**Custo via API (modelo barato):** **~R$ 0,30/prova** (gpt-5-mini/Gemini Flash), zero capex, escala elástica, melhor qualidade.

**Crossover detalhado (com luz + amortização + manutenção):**

O custo local é quase todo **fixo** (capex amortizado + energia 24/7), independente do volume até o teto de throughput. Custo de energia no Brasil ~R$ 0,90/kWh (comercial). Amortização do hardware em 3 anos.

| Setup local | Capex | Amortização/ano | Energia/ano (24/7) | **Custo fixo/ano** | Modelo que roda |
|---|---|---|---|---|---|
| RTX 3090 (usada ~R$ 6k) | R$ 6.000 | R$ 2.000 | ~R$ 4.700 (rig ~600W) | **~R$ 6.800/ano** | até ~30B (qualidade < gpt-5-mini) |
| A6000 48GB | R$ 48.000 | R$ 16.000 | ~R$ 7.000 (rig ~800W) | **~R$ 23.000/ano** | 70B (mais perto de frontier) |

**Comparação API × local por volume:**

| Provas/ano (≈ alunos) | API (R$ 0,30/prova) | Local 3090 (~R$ 6,8k fixo) | Local A6000 (~R$ 23k fixo) |
|---|---|---|---|
| 23 mil (~2.300 alunos) | R$ 6,9k | **R$ 6,8k (empata)** | R$ 23k |
| 77 mil (~7.700 alunos) | R$ 23k | R$ 6,8k | **R$ 23k (empata)** |
| 500 mil (~50 mil alunos) | **R$ 150k** | R$ 6,8k* | R$ 23k* |
| 1 milhão (~100 mil alunos) | **R$ 300k** | — | R$ 23–94k (multi-GPU) |

\* uma GPU só **pode não dar conta do throughput** nesse volume — precisaria de várias.

**Conclusão honesta do crossover:**
- **< ~2.300 alunos:** API ganha claramente (capex parado não compensa).
- **2.300–50.000 alunos:** o local "empata ou ganha no papel", **mas a economia é de poucos milhares de reais** e você herda **ops + risco de qualidade inferior** do modelo open-source. **API ainda recomendado** por simplicidade e qualidade.
- **50.000+ alunos (Salta/público):** aí o local pode economizar **R$ 100 mil+/ano** — vale o projeto de validar um modelo open-source dedicado. É o estágio em que faz sentido investir na GPU, provavelmente combinado com o gatilho de privacidade.

> **Recomendação:** **API agora**; reabrir a conta do GPU local **só ao cruzar ~50 mil alunos** (ou se a privacidade exigir antes).
>
> **Nota LGPD/jurídico:** mandar prova de aluno para API de terceiro tem implicação legal — **fica para o advogado do investidor resolver depois do aporte** (decisão do Otavio: não é prioridade de pesquisa agora).

### Equipe (compõe o burn de R$ 40 mil/mês)

| Cargo | Base/mês | Carregado CLT (~80% encargos) |
|---|---|---|
| Backend pleno | R$ 7.800 | ~R$ 14.000 |
| Designer pleno (UI/UX) | R$ 5.500–6.000 | ~R$ 10.000 |
| Founder (pró-labore) | R$ 10.000 | R$ 10.000 |
| Infra + contador + ferramentas | — | ~R$ 5.000 |
| **Total burn** | — | **~R$ 39–40 mil/mês** |

- Júnior/sênior para referência: designer júnior ~R$ 3–3,5k, sênior ~R$ 9–12k; backend júnior ~R$ 3,4–4,5k, sênior ~R$ 12,4–20,9k. PJ costuma ficar ~20–40% acima do CLT-base.
- **A IA (R$ 0,30/prova) é ~1% do custo;** o burn é **97% equipe**. O gargalo de custo é gente, não modelo.

---

## Modelo de ROI — premissa R$ 20/aluno/mês (escolhida pelo Otavio)

> Premissa de trabalho (não é o modelo de negócio fechado, é a régua para dimensionar reais e tempo de retorno):
> aluno paga **R$ 200/mês** por todos os serviços, dos quais **R$ 20/mês vão para o NOVO CR**.
> Isso é **R$ 240/aluno/ano** (12 meses) — ~R$ 200 se considerar ano letivo de 10 meses. 🟡

**Premissas:** lucro do NOVO CR varia de **R$ 5 a R$ 20 por aluno/mês** (já líquido do custo de IA, que é centavos). Burn de equipe (designer + backend pleno + founder, CLT carregado): **~R$ 40 mil/mês**.

### A) Receita anual do NOVO CR (lucro/aluno/mês × nº de alunos)

| N alunos | R$ 5/mês | R$ 10/mês | R$ 15/mês | R$ 20/mês |
|---|---|---|---|---|
| **5.000** (piloto) | R$ 300 mil | R$ 600 mil | R$ 900 mil | R$ 1,2 mi |
| **9.000** (FGV) | R$ 540 mil | R$ 1,08 mi | R$ 1,62 mi | R$ 2,16 mi |
| **10.000** | R$ 600 mil | R$ 1,2 mi | R$ 1,8 mi | R$ 2,4 mi |
| **50.000** (Salta-RJ) | R$ 3,0 mi | R$ 6,0 mi | R$ 9,0 mi | R$ 12 mi |
| **100.000** (Salta total) | R$ 6,0 mi | R$ 12 mi | R$ 18 mi | R$ 24 mi |

### B) Breakeven operacional (alunos para cobrir o burn de R$ 40 mil/mês)

| Lucro/aluno/mês | Alunos p/ breakeven |
|---|---|
| R$ 5 | **8.000** |
| R$ 10 | **4.000** |
| R$ 15 | **2.667** |
| R$ 20 | **2.000** |

### C) Caixa mensal para pagar o investimento (Net/mês = lucro×N − R$ 40 mil)

| N alunos | R$ 5/mês | R$ 10/mês | R$ 15/mês | R$ 20/mês |
|---|---|---|---|---|
| 5.000 | −R$ 15 mil | +R$ 10 mil | +R$ 35 mil | +R$ 60 mil |
| 10.000 | +R$ 10 mil | +R$ 60 mil | +R$ 110 mil | +R$ 160 mil |
| 50.000 | +R$ 210 mil | +R$ 460 mil | +R$ 710 mil | +R$ 960 mil |
| 100.000 | +R$ 460 mil | +R$ 960 mil | +R$ 1,46 mi | +R$ 1,96 mi |

> **Payback (meses) = Investimento ÷ Net/mês.** Ex.: round de R$ 400 mil, 10 mil alunos a R$ 10/mês → 400÷60 ≈ **~7 meses**. A R$ 20/mês → 400÷160 ≈ **~2,5 meses**.

**Leituras:**
- O **piso (R$ 5/mês)** ainda é um bom negócio: 50 mil alunos (Salta-RJ) = **R$ 3 mi/ano**; 100 mil = **R$ 6 mi/ano**.
- O **breakeven** é o número que importa no curto prazo: a R$ 10/mês bastam **4.000 alunos** para a operação se pagar. Um piloto Pensi de 5–10 mil já passa disso.
- **Só Salta + FGV** (≈ 109 mil alunos): de **R$ 6,5 mi/ano** (a R$ 5) a **R$ 26 mi/ano** (a R$ 20).
- **Ressalva 1:** o relógio do payback só começa quando os alunos estão *ativos*; a rampa de venda adiciona meses na frente.
- **Ressalva 2:** R$ 20/mês só se sustenta vendido **embutido numa mensalidade** (≈ 1–2% de uma mensalidade de R$ 1.000–3.000). O piso de R$ 5/mês é mais conservador e ainda fecha a conta.

---

## Comparação dos 3 modelos de negócio — quanto cada um paga

> Premissas: aluno faz **~10 provas/ano**; custo de API ~R$ 0,30/prova; Pensi/Salta RJ ≈ 55 unidades.
> Preços-base por modelo: **A)** R$ 3/prova corrigida (conservador — Imaginie cobra R$ 7–10 por *redação*),
> **B)** R$ 20/aluno/ano (faixa Turnitin), **C)** R$ 20 mil/escola/ano (referência MagicSchool US$ 3.999). 🟡

| Cenário | A) Por correção (R$ 3/prova) | B) Por aluno/ano (R$ 20) | C) Por escola/ano (R$ 20 mil) |
|---|---|---|---|
| **Piloto Pensi** (10 mil alunos ≈ 10 escolas) | **R$ 300 mil** | R$ 200 mil | R$ 200 mil |
| **Marcas RJ inteiras** (50 mil alunos ≈ 55 unidades) | **R$ 1,5 mi** | R$ 1,0 mi | R$ 1,1 mi |
| **SEEDUC** (600 mil alunos ≈ 1.200 escolas) | R$ 18 mi nominal (negociado ~R$ 6 mi a R$ 1/prova) | R$ 12 mi | R$ 24 mi nominal (negociado) |

**Trade-offs:**
- **A) Por correção** — paga mais SE o uso for alto; risco de receita baixa se a escola usar pouco; exige medir/cobrar por volume. Melhor alinhamento custo-receita (custo também é por prova).
- **B) Por aluno/ano** — receita previsível (ARR limpo para pitch de investimento); risco de "all-you-can-eat" se usarem muito (mitigado: custo é centavos). **Validado no BR: é o modelo da Letrus ("mensalidade por aluno atendido").**
- **C) Por escola/ano** — o mais simples de aprovar numa controladoria (1 número × 55 unidades); perde granularidade (escola grande paga igual à pequena).
- Os três convergem em ordem de grandeza (~R$ 200–300 mil no piloto; ~R$ 1–1,5 mi nas marcas RJ). **A escolha é mais sobre facilidade de venda e previsibilidade do que sobre o tamanho do cheque.**

---

## Dossiê 1/3 — Letrus (o concorrente a copiar e a evitar)

| Dimensão | Dado | Flag |
|---|---|---|
| Fundação | 2017 — Luis Junqueira + Thiago Rached | 🟢 |
| **Captação total** | **R$ 96 milhões** desde 2017; última rodada **R$ 36 mi** (Crescera Capital + Owl Ventures; com BID Lab, **Fundação Lemann**, VélezReyez+ (David Vélez/Nubank), Altitude/Península) | 🟢 |
| **Modelo de negócio** | **Mensalidade por aluno atendido** (B2B) — valida o modelo "por aluno" no Brasil | 🟢 |
| Clientes privados | Pueri Domus, Bahema, **SESI**; **630–680 escolas** no total | 🟢 |
| Escala | **~450 mil alunos já impactados** (atingido, cumulativo — inclui pilotos públicos gratuitos, ≠ base pagante); **meta declarada: 1 milhão em 2 anos** | 🟢 |
| Setor público | Entra **de graça** (MS: 48 mil alunos), depois converte em política pública (GO, ES, MT) | 🟢 |
| Produto | Só **redação/escrita** (gêneros de vestibular); professor escolhe tema, aluno digita, IA corrige na hora, professor valida | 🟢 |
| Reconhecimento | Prêmio UNESCO de melhor tecnologia educacional | 🟢 |

**O que copiar da Letrus:**
1. Modelo "mensalidade por aluno" — investidores brasileiros já validaram com R$ 96 mi.
2. Motion dupla: redes privadas (Pueri Domus/Bahema/SESI = decisor central, como o Salta) + público via piloto gratuito.
3. "Professor valida a IA" — mesma filosofia do pipeline transparente do NOVO CR.

**Onde a Letrus é vulnerável (sua abertura) — ✅ as 3 validadas pelo Otavio como diferencial do NOVO CR:**
1. **Só corrige redação.** Prova de matemática, ciências, múltipla escolha + discursiva mista — fora do alcance dela. NOVO CR corrige prova inteira, qualquer matéria.
2. Aluno **digita** o texto — a Letrus não lê prova manuscrita/escaneada. **O NOVO CR lê foto/scan de prova feita no papel** (como as escolas realmente aplicam) — diferença operacional grande.
3. Com R$ 96 mi captados, pressão de escala nacional padronizada — **pouco incentivo para virar fornecedor dedicado** de uma rede (Salta) ou da FGV. O NOVO CR pode ser o parceiro sob medida.

> **Ressalva honesta:** nenhuma dessas é um fosso tecnológico permanente — uma equipe de R$ 96 mi copia features. O fosso real precisa vir de **relacionamento (sócio no Salta, contatos na Prefeitura) + foco/customização**, não só de produto.

**Régua de benchmark:** Letrus levou ~7 anos e R$ 96 mi para chegar a 680 escolas / 450 mil alunos. Os alvos do Otavio: **Grupo Salta inteiro (>117 mil alunos)** + **FGV (~9 mil alunos)** + setor público RJ na sequência — ou seja, o plano mira ~28% da escala da Letrus já nos dois primeiros contratos-âncora, com fração do capital dela.

---

## Dossiê 2/3 — Imaginie (a maior em volume, mas híbrida e lenta)

| Dimensão | Dado | Flag |
|---|---|---|
| Posição | **Maior empresa de correção de redação do Brasil**, ~10 anos de operação | 🟢 |
| **Modelo de correção** | **Híbrido: IA + corretores humanos** (voluntários) — prazo de **15 dias** para nota final | 🟢 |
| **Modelo de negócio** | **Crédito por correção** (1 crédito = 1 redação): R$ 9,90 avulso, R$ 69,90 o pacote de 10 (R$ 7/un); planos escola a partir de R$ 69/mês; "redes compram **milhares de créditos/ano**" | 🟢 |
| Produto p/ aluno | ENEM 900+ 12× R$ 21; pacotes; relatórios por competência do ENEM | 🟢 |
| Setor público | **MG: +142 mil redações** corrigidas (IA + revisão humana) — atua no público como a Letrus | 🟢 |
| Capital | Plataforma desenvolvida com **+R$ 1 milhão** (modesto vs Letrus R$ 96 mi) | 🟢 |

**O que a Imaginie valida para você:**
1. **O modelo "por correção" funciona e escala** — redes compram milhares de créditos/ano a ~R$ 7/correção. Isso prova o seu **Modelo A** (por prova).
2. O mercado paga **R$ 7–10 por redação corrigida** — e seu custo com IA pura é ~R$ 0,30. Margem enorme.
3. Dá para atender público E privado com o mesmo produto.

**Onde a Imaginie é vulnerável (sua abertura) — ⚠️ reframe importante:**

> **O NOVO CR NÃO é "IA sem humano".** Ele é um **assistente do professor**: gera o rascunho de correção na hora, o professor **revisa e dá a nota final** gastando uma fração do tempo. O pitch certo é *"o professor corrige 5× mais rápido com output melhor"*, não *"trocamos o professor por IA"*.

1. **Imaginie usa corretores SEPARADOS (voluntários) → 15 dias de prazo.** Depende da disponibilidade desses voluntários. O NOVO CR usa **o professor que já ia corrigir** — rascunho instantâneo + revisão dele = sem fila, sem terceiro.
2. **Só redação** (mesma limitação da Letrus) — não corrige prova inteira/multimatéria.
3. Plataforma de **+R$ 1 mi** (capital modesto) — concorrente "batível" em tecnologia.

> **A revisão humana é uma FORÇA, não defeito** (tanto da Imaginie quanto do NOVO CR) — é o que dá confiança ao resultado. A diferença é que no NOVO CR o revisor é o próprio professor, no fluxo dele, sem prazo de 15 dias.

> **Leitura combinada Letrus + Imaginie:** as duas maiores do BR **só fazem redação** e a maior em volume **ainda depende de humano**. O espaço de "**prova completa, multimatéria, 100% IA, instantânea, em PT-BR**" segue vazio.

---

## Dossiê 3/3 — Gradescope/Turnitin (o único que faz prova inteira — e a real ameaça de entrada)

| Dimensão | Dado | Flag |
|---|---|---|
| Dono | **Turnitin** (adquirida por ~US$ 1,75 bi em 2019) | 🟢 |
| Escala | **110–140 mil instrutores, ~2,7–3,2 mi alunos, 2.600 instituições** | 🟢 |
| Foco | **Universidade** (EUA), com uso secundário em ensino médio | 🟢 |
| Produto | Lê **prova manuscrita** (inglês + notação matemática), múltipla escolha, código; **agrupa respostas semelhantes** (answer groups) | 🟢 |
| **Tipo de IA** | **NÃO é IA generativa** — usa OCR + algoritmos de **clustering/reconhecimento**. "A IA sugere agrupamentos; o instrutor revisa, ajusta e aplica a rubrica. Nota e feedback finais = humano." | 🟢 |
| Preço | US$ 1–3/aluno/curso; institucional ~US$ 4/aluno (caso UGA) | 🟢 |
| **Português** | ⚠️ **Disponível em português (BR) desde maio/2022** (+ japonês, coreano, espanhol, turco) | 🟢 |

**Por que o Gradescope importa — é o concorrente mais perigoso (a real ameaça de entrada):**
- É o **único** que já faz "prova inteira / manuscrito / multimatéria" — exatamente o espaço do NOVO CR.
- **Já está em português** e tem o capital da Turnitin (US$ 1,75 bi) atrás.

**Mas é fundamentalmente diferente do NOVO CR (suas aberturas):**
1. **Clustering, não IA generativa.** O Gradescope **agrupa respostas parecidas** para o professor corrigir um lote de uma vez — ele **não lê, entende e dá nota+feedback por aluno** numa resposta discursiva aberta. O NOVO CR (LLMs multi-provider) **faz a correção substantiva** e gera feedback individual. Em prova discursiva aberta, o Gradescope só organiza; o NOVO CR corrige.
2. **Exige template rígido** (resposta em uma linha, caixa demarcada). O NOVO CR lê a prova **como ela é aplicada** no papel.
3. **Universitário e americano.** Interface em PT, mas **sem contexto pedagógico brasileiro** (ENEM, BNCC, vestibular) e sem foco em educação básica.

> **Confirma a filosofia do NOVO CR:** o líder global também é **human-in-the-loop** ("nota e feedback finais = humano"). Logo, "o professor revisa" não é fraqueza — é o padrão da categoria.

> **Ameaça a declarar no pitch (honestidade):** se a Turnitin resolver plugar IA generativa no Gradescope e empurrar para o K-12 brasileiro, é o concorrente a observar. A defesa do NOVO CR: **velocidade de execução, foco em educação básica BR e relacionamento (Salta, FGV, Prefeitura)** — antes que um gigante americano olhe para cá.

---

## Tese central do posicionamento (✅ decisão Otavio: "oceano azul / categoria nova")

> **"O mercado de correção por IA no Brasil é 100% redação e penetra <1% das escolas. O NOVO CR abre uma categoria nova — prova inteira, multimatéria — que nenhum player relevante atende. Não disputo o bolo da redação; abro o bolo dos outros 99%."**
>
> Lastro: Letrus/Imaginie/Cria só fazem redação (~1.600 escolas, <1% das 179 mil do país); o único que faz prova inteira (Gradescope) é clustering americano universitário, não correção generativa de educação básica BR.

---

## Funil de conversão no setor público (motion "doar → contrato")

> A jogada da Letrus, aplicada ao NOVO CR no Rio. Otavio tem contatos na **Prefeitura do Rio**.
> Sequência: **doar piloto pequeno → provar impacto → converter via licitação em contrato grande.**

### Etapa 1 — Doar o piloto (custo de aquisição)

| Item | Estimativa | Flag |
|---|---|---|
| Tamanho do piloto | 5.000 alunos — **✅ decisão Otavio: rodar nos GEC/GET** (Ginásios Experimentais, vitrine de inovação da prefeitura) | — |
| Preço do contrato | **✅ decisão Otavio: definir após o piloto** (em função do impacto/economia comprovada) | — |
| Custo de IA | 5.000 × ~10 provas/ano × ~R$ 0,30 = **~R$ 15 mil/ano** | 🟡 |
| Suporte + onboarding (tempo de equipe) | ~R$ 20–35 mil/ano | 🟡 |
| **Custo total de "doar"** | **~R$ 35–50 mil** por ~6–12 meses | 🟡 |

> Ou seja: doar para 5 mil alunos custa o equivalente a **~1 mês de folha**. É marketing barato, não filantropia cara.

### Etapa 2 — Provar impacto (a moeda da conversão)

Métricas que viram case: nota média ↑, **horas de professor economizadas**, % de provas corrigidas no prazo, engajamento. Esse case é o que destrava a licitação e serve de marketing para o privado também.

### Etapa 3 — Converter em contrato grande (o retorno)

**Quanto vale um contrato público de 100 mil alunos?** Faixa por preço/aluno/ano:

| Preço/aluno/ano | 100 mil alunos | Referência |
|---|---|---|
| R$ 5 (piso público) | **R$ 500 mil/ano** | abaixo de Turnitin público (US$ 1,79 ≈ R$ 9,5) |
| R$ 10 | **R$ 1,0 mi/ano** | ~Turnitin público (US$ 2 ≈ R$ 10) |
| R$ 15 | **R$ 1,5 mi/ano** | meio da faixa Turnitin |
| R$ 20 (nível privado) | **R$ 2,0 mi/ano** | teto otimista p/ público |

**Retorno sobre o piloto:** custo de aquisição ~R$ 35–50 mil → contrato de **R$ 500 mil – R$ 2 mi/ano** = **ROI de 10x a 40x** sobre o piloto, recorrente. 🟡

### Âncoras reais de gasto público em edtech (mostram que o governo paga)

| Contrato | Valor | Por aluno | Observação |
|---|---|---|---|
| MS — cursos técnicos (12 mil alunos) | R$ 94,1 mi | ~R$ 7.840 | Pacote completo de cursos (não comparável, mas mostra escala) |
| Amazonas — rede estadual inteira | R$ 1,35 **bilhão** | — | Pacote total (material+pedagogia+portal+avaliação) |
| MG — livros didáticos (3 anos) | R$ 848 mi | — | Mostra apetite de gasto |

> Leitura: uma ferramenta **só de correção** é uma linha pequena perto desses pacotes — **mais fácil de aprovar** e cabe em qualquer orçamento. R$ 5–15/aluno é realista para escopo estreito.

### Riscos do funil público (declarar no pitch)

- **Licitação é lenta** (12–24 meses) e formal — exige LGPD, servidor nacional, edital.
- **Risco eleitoral/político** — troca de gestão pode esfriar o contrato.
- **Governo paga atrasado** — fluxo de caixa exige colchão.
- **Conversão não é garantida** — por isso o piloto tem que ter custo baixo (etapa 1) e métricas fortes (etapa 2).

---

## Market share — quanto os concorrentes têm e quanto dá pra tomar

### O mercado total (Censo Escolar 2024, INEP)

| Recorte | Alunos | Escolas |
|---|---|---|
| **Educação básica (total Brasil)** | **47,1 milhões** | **179,3 mil** |
| Ensino médio (onde prova é mais intensa) | 7,8 milhões | — |
| — estadual | 6,5 mi (83%) | — |
| — privada | ~1,0 mi (13%) | — |
| — federal | 243,6 mil (3%) | — |
| EJA | 2,4 milhões | — |

### O que os concorrentes (de correção por IA) realmente detêm

| Player | Base de alunos | Instituições | Foco | Observação |
|---|---|---|---|---|
| **Imaginie** | ~**3 mi cadastrados** (downloads do app) | **800** | só redação | "cadastrado" ≠ pagante; 800 escolas é o proxy B2B real; ~40 mil redações/mês |
| **Letrus** | ~450 mil impactados | 680 | só redação | inclui pilotos públicos gratuitos |
| **Cria** | 240 mil | 120 | só redação (ENEM) | freemium |
| **Soma (redação BR)** | — | **~1.600 escolas** | **100% redação** | **≈ 0,9% das 179,3 mil escolas do país** |

### O insight de share

- O mercado de **correção por IA no Brasil é 100% redação** e penetra **<1% das escolas** (~1.600 de 179,3 mil). Mesmo a líder (Imaginie, 800 escolas) tem **<0,5%** das escolas.
- **O espaço do NOVO CR (prova inteira, multimatéria) tem 0 player relevante.** Não é dividir o bolo da redação — é abrir o bolo dos **outros 99%** (provas de todas as matérias, todas as séries).
- **Tamanho do espaço vazio (ilustrativo):** capturar só **1% das escolas do país** (~1.790 escolas × ~500 alunos = ~900 mil alunos) a R$ 10/aluno/mês = **~R$ 108 mi/ano**. O TAM é gigante porque ninguém atende.

### Quanto dá pra tomar no curto prazo (SAM realista do Otavio)

| Beachhead | Alunos | Receita/ano a R$ 5–20/mês |
|---|---|---|
| Grupo Salta (privado, sócio) | 117 mil | R$ 7–28 mi |
| FGV | 9 mil | R$ 0,5–2,2 mi |
| Federais RJ (CPII, IFRJ, CEFET — prestígio) | 40–50 mil | R$ 2,4–12 mi |
| Público RJ via piloto GEC → licitação | 100 mil+ | R$ 6–24 mi |

> Nenhum desses está "tomado" por um concorrente de **prova inteira** — porque ele não existe. A disputa, quando houver, é contra correção manual do professor (status quo), não contra Letrus/Imaginie (que só fazem redação).

---

## Os 3 fatos que mudam a conversa (achados das pesquisas)

1. **O preço da categoria é baixo e por volume.** Turnitin cobra US$2–6/aluno/ano de universidades americanas. Isso significa: ninguém fica rico com 1 escola — o jogo é **contrato-âncora com rede** (Salta, SEEDUC). Por isso o split 1.4.1 (Rio vs fora) importa: o Salta dá acesso a 117 mil alunos com **um** decisor.

2. **A Letrus entra de graça para depois virar política pública.** Em MS a plataforma entrou "a título gratuito" — depois vira contrato estadual. Estratégia validada para o setor público BR: **piloto gratuito → prova de impacto → licitação**. O NOVO CR pode replicar com os GECs/GETs (~11-30 mil alunos, perfil inovador, vitrine da prefeitura).

3. **O nicho exato do NOVO CR está vazio.** Letrus/Cria = só redação. Gradescope = prova inteira mas inglês/universidade. **Prova completa multi-questão em PT-BR para educação básica = ninguém.** É o pitch de uma frase.

---

## Perguntas abertas (próximas rodadas de pesquisa)

- [ ] Valor real dos contratos Letrus (exige garimpar portais de transparência estaduais — GO/ES/MT)
- [ ] Split de alunos (não unidades) do Salta Rio vs fora — relatório de RI
- [x] Quanto custa por prova corrigida via API hoje no NOVO CR? → **estimado em ~R$ 0,15–0,50/prova** (ver seção "Custo por prova"). Confirmar com tokens reais de um run do pipeline.
- [ ] Ticket que escolas privadas pagam por sistemas de ensino (benchmark de orçamento disponível)
- [ ] Processo de licitação SEEDUC: o que exige (segurança, LGPD, servidor nacional?)

---

## Fontes-chave desta síntese

- [Gradescope — pricing institucional](https://info.gradescope.com/pricing) e [caso Univ. Georgia (~US$4/aluno/curso)](https://kb.franklin.uga.edu/display/public/FOKFC/Gradescope)
- [The Markup — Turnitin cobrou US$1,79–6,50/aluno de faculdades da Califórnia](https://themarkup.org/artificial-intelligence/2025/06/26/plagiarism-detector-costs-california)
- [CoGrader — US$19/mês](https://cograder.com/)
- [SED-MS — Letrus inserida "a título gratuito" (48 mil alunos)](https://www.sed.ms.gov.br/159-escolas-da-rede-estadual-de-ensino-sao-inseridas-no-programa-letrus-de-desenvolvimento-de-escrita/)
- [Letrus — 450 mil alunos impactados, 27 UFs](https://www.letrus.com/)
- Documentos-base: `01_alunos_rio_e_fgv.md`, `02_concorrentes.md`, `03_custos_infra_e_equipe.md`
