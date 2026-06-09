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

**Preços de referência da categoria (o achado mais importante desta rodada):**
- **Gradescope:** US$1–3/aluno/curso (individual); institucional ~**US$4/aluno/curso/ano** (caso real: Univ. da Geórgia) 🟢
- **Turnitin:** **US$1,79–6,50/aluno/ano** (California State pagou US$2,59 em 2024 — registros de compras públicas) 🟢
- **CoGrader:** **US$19/professor/mês** 🟢
- **Letrus:** preço não público; em MS a parceria foi **gratuita** (estratégia de prova social/filantropia para depois vender) 🟢
- Em reais: a categoria cobra algo como **R$ 10–35 por aluno/ano** (B2B institucional) ou **R$ 100–150/professor/mês** (B2C professor). 🟡 (conversão ~R$5,3/US$)

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

### Custos vs ganhos (margem)
- Equipe-núcleo: ~R$ 13–14 mil/mês base (designer pleno + backend pleno) → **~R$ 160–340 mil/ano** com encargos 🟢
- Infra: APIs de IA (variável por correção, centavos por prova) ou GPU local R$ 5–19 mil one-off
- **Breakeven do Cenário 1-2:** entre R$ 300–500 mil ARR a operação se paga com equipe mínima. 🟡

---

## Os 3 fatos que mudam a conversa (achados das pesquisas)

1. **O preço da categoria é baixo e por volume.** Turnitin cobra US$2–6/aluno/ano de universidades americanas. Isso significa: ninguém fica rico com 1 escola — o jogo é **contrato-âncora com rede** (Salta, SEEDUC). Por isso o split 1.4.1 (Rio vs fora) importa: o Salta dá acesso a 117 mil alunos com **um** decisor.

2. **A Letrus entra de graça para depois virar política pública.** Em MS a plataforma entrou "a título gratuito" — depois vira contrato estadual. Estratégia validada para o setor público BR: **piloto gratuito → prova de impacto → licitação**. O NOVO CR pode replicar com os GECs/GETs (~11-30 mil alunos, perfil inovador, vitrine da prefeitura).

3. **O nicho exato do NOVO CR está vazio.** Letrus/Cria = só redação. Gradescope = prova inteira mas inglês/universidade. **Prova completa multi-questão em PT-BR para educação básica = ninguém.** É o pitch de uma frase.

---

## Perguntas abertas (próximas rodadas de pesquisa)

- [ ] Valor real dos contratos Letrus (exige garimpar portais de transparência estaduais — GO/ES/MT)
- [ ] Split de alunos (não unidades) do Salta Rio vs fora — relatório de RI
- [ ] Quanto custa por prova corrigida via API hoje no NOVO CR? (dado interno — define margem)
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
