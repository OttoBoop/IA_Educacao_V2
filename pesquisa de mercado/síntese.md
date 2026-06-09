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

**Onde a Imaginie é vulnerável (sua abertura):**
1. **Híbrido = lento e caro.** Depende de corretor humano → **15 dias** de prazo e custo de mão de obra por correção. O NOVO CR é **IA pura: instantâneo e com margem muito maior** (não paga corretor).
2. **Só redação** (mesma limitação da Letrus) — não corrige prova inteira/multimatéria.
3. Plataforma de **+R$ 1 mi** (não é gigante de capital) — concorrente "batível" em tecnologia, ao contrário da Letrus.

> **Leitura combinada Letrus + Imaginie:** as duas maiores do BR **só fazem redação** e a maior em volume **ainda depende de humano**. O espaço de "**prova completa, multimatéria, 100% IA, instantânea, em PT-BR**" segue vazio.

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
