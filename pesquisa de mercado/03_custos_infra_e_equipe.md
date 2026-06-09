# Pesquisa 03 — Custos: Infra (GPU) e Equipe

> Bloco 3. **Todos os valores em BRL** (referência USD entre parênteses quando a cotação original é em dólar).
> Flag: 🟢 dado de fonte / 🟡 estimativa. Preços de hardware variam muito — faixas de jun/2026.

---

## 3.1 Placa de vídeo para rodar modelos open-source localmente

### Regra de dimensionamento (VRAM)

- **Fórmula prática (quantização Q4):** `VRAM (GB) ≈ tamanho do modelo (B) ÷ 8`. 🟢
- Q4_K_M reduz ~75% da VRAM vs FP16 mantendo boa qualidade.
- O **contexto longo** infla o KV-cache: um modelo 8B vai de ~0,3 GB (2K tokens) a ~5 GB (32K) e ~20 GB (128K) só de cache.

| Tier do modelo | VRAM mínima (Q4) | GPU recomendada | Preço aprox. BRL | Flag |
|---|---|---|---|---|
| **7–8B** (ex.: Llama 3 8B, Mistral 7B) | ~5–6 GB (8 GB folgado) | **RTX 3060 12GB** | **~R$ 2.400** | 🟢 |
| **13–14B** | ~8–10 GB (12 GB no limite) | RTX 3060 12GB / RTX 4070 | **~R$ 2.400–4.500** | 🟢/🟡 |
| **30–34B** | ~18–24 GB | **RTX 3090 24GB** / RTX 4090 24GB | **~R$ 6.000–20.000** (usada vs nova) | 🟢 |
| **70B** | ~42 GB+ (precisa 2 GPUs ou 48GB) | **2× RTX 4090** ou **1× RTX A6000 48GB** | **2× ~R$ 20.000 = ~R$ 40.000** ou **A6000 ~R$ 48.000** | 🟢 |
| **Profissional/data-center** | 80 GB | NVIDIA H100/A100 (mais comum **alugar na nuvem**) | dezenas de milhares de USD (não-varejo) | 🟡 |

### Preços de varejo BR observados (jun/2026)

- **RTX 3060 12GB:** **~R$ 2.439** 🟢 (entrada — roda 7B confortável, 13B no limite)
- **RTX 3090 24GB:** **~R$ 5.000 (usada) a ~R$ 18.900 (nova/varejo)** 🟢 (custo-benefício para 30B+ por causa dos 24GB)
- **RTX 4090 24GB:** **~R$ 20.000 a ~R$ 27.700** 🟢
- **RTX A6000 48GB (profissional):** **~R$ 48.000** 🟢 (lançada a US$4.650; cabe um 70B Q4 numa placa só)

> **Recomendação para o NOVO CR:** rodar localmente só faz sentido para modelos pequenos/médios (7B–34B). Para isso, **RTX 3090 24GB (~R$ 5–19 mil)** é o melhor custo-benefício (24GB cobrem até ~34B e contexto razoável). Para 70B, o custo de hardware (~R$ 40–48 mil) + energia geralmente perde para **APIs/nuvem sob demanda** no estágio atual — usar local apenas se houver requisito de privacidade ou volume muito alto e constante.

---

## 3.2 Designer (UX/UI) — por mês (BRL)

| Nível | Faixa mensal (BRL) | Flag |
|---|---|---|
| **Média geral (CAGED)** | **~R$ 3.725** (jornada 43h); faixa R$ 2.401–7.019 | 🟢 |
| **Júnior** | **~R$ 3.000–3.500** | 🟢 |
| **Pleno** | **~R$ 5.500–6.000** | 🟢 |
| **Sênior** | **~R$ 9.000–12.000** (≈R$ 10.000 típico) | 🟢 |
| **CLT** (geral) | R$ 3.000–7.500 (até ~R$ 12.500 no topo) | 🟢 |
| **PJ / freelance** | R$ 5.000–9.000 (até ~R$ 15.000 no topo) | 🟢 |

> **Para o NOVO CR:** um designer **pleno** (~R$ 5.500–6.000/mês CLT, ou ~R$ 7–9 mil PJ) cobre bem UI de produto. Para algo pontual, freelancer por projeto pode ser mais barato que contratar.

---

## 3.3 Desenvolvedor Backend — por mês (BRL)

| Nível | Faixa mensal (BRL) | Flag |
|---|---|---|
| **Média geral** | **~R$ 5.945** (jornada 42h) | 🟢 |
| **Júnior** (até ~2 anos) | **~R$ 3.355–4.500** | 🟢 |
| **Pleno** | **~R$ 7.800** | 🟢 |
| **Sênior** (5+ anos, liderança técnica) | **~R$ 12.400–20.900** (≈R$ 12.500 base) | 🟢 |

> **Para o NOVO CR:** um backend **pleno** (~R$ 7.800/mês CLT) é o ponto de equilíbrio para tocar o pipeline (FastAPI, integrações de IA). Sênior (R$ 12–20 mil) se precisar de arquitetura/escala. PJ costuma ficar ~20–40% acima do CLT-base.

---

## Resumo do Bloco 3

| Item | Valor (BRL) | Flag |
|---|---|---|
| 3.1 GPU 7–8B (RTX 3060 12GB) | ~R$ 2.400 | 🟢 |
| 3.1 GPU 30B+ (RTX 3090 24GB) | ~R$ 5.000–19.000 | 🟢 |
| 3.1 GPU 70B (2× 4090 ou A6000 48GB) | ~R$ 40.000–48.000 | 🟢 |
| 3.2 Designer pleno | ~R$ 5.500–6.000/mês | 🟢 |
| 3.3 Backend pleno | ~R$ 7.800/mês | 🟢 |

**Custo mínimo mensal de equipe (1 designer pleno + 1 backend pleno, CLT-base):** **~R$ 13.000–14.000/mês** (sem encargos; com encargos CLT, somar ~70–100%).

## Fontes

- [Local AI Master — VRAM Requirements 2026 (7B/13B/70B)](https://localaimaster.com/blog/vram-requirements-2026)
- [LocalLLM.in — Ollama VRAM Requirements 2026](https://localllm.in/blog/ollama-vram-requirements-for-local-llms)
- [EaseCloud — Run 70B LLMs on Consumer GPU](https://blog.easecloud.io/ai-cloud/run-70b-models-on-consumer-gpus/)
- [KaBuM! — RTX 3090 / placas de vídeo (preços BR)](https://www.kabum.com.br/busca/placa-de-video-rtx-3090)
- [Mercado Livre — RTX 4090 (preços BR)](https://lista.mercadolivre.com.br/rtx-4090)
- [KaBuM! — RTX A6000 48GB PNY](https://www.kabum.com.br/produto/459501/placa-de-video-pny-nvidia-quadro-rtx-a6000-48gb-gddr6-384bits-vcnrtxa6000-pb)
- [TudoCelular — RTX A6000 lançada a US$4.650](https://www.tudocelular.com/novos-produtos/noticias/n167729/nvidia-rtx-a6000-e-lancada-ga102-e-48gb-de-vram.html)
- [Salario.com.br — Designer de UX (CBO 262410)](https://www.salario.com.br/profissao/designer-ux-cbo-262410/)
- [Indeed — Quanto ganha um UX designer](https://br.indeed.com/conselho-de-carreira/pagamento-salario/quanto-ganha-ux-designer)
- [Salario.com.br — Desenvolvedor back-end](https://www.salario.com.br/profissao/desenvolvedor-back-end/)
- [Hora de Codar — Salário desenvolvedor júnior/pleno/sênior](https://horadecodar.com.br/salario-desenvolvedor/)
- [Robert Half — Desenvolvedor Back-End Sênior 2026](https://www.roberthalf.com/br/pt/vagas-detalhes/desenvolvedora-back-end-senior)
