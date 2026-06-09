# Pesquisa 02 — Concorrentes do NOVO CR

> Bloco 2. Escopo definido pelo Otavio: **Brasil + players globais de IA**.
> Flag: 🟢 dado de fonte / 🟡 estimativa. Fontes consultadas jun/2026.

## Enquadramento: o que é "igual" ao NOVO CR?

O NOVO CR é uma **plataforma de correção automática de provas/atividades por IA** com geração de feedback detalhado, voltada a professores/instituições. O concorrente "igual" não é a Descomplica — é a categoria **AI grading / automated essay scoring (AES)**. A Descomplica é **adjacente** (edtech de ensino/cursinho/graduação), não um corretor automático.

Dois grupos:
1. **Correção por IA (concorrentes diretos)** — fazem o mesmo "job": corrigir provas/redações automaticamente.
2. **Edtechs amplas (concorrentes indiretos/adjacentes)** — disputam orçamento e atenção de escolas/alunos, mas o produto-núcleo é outro (ensino, cursinho, graduação).

---

## Grupo 1 — Correção por IA (concorrentes diretos)

### Brasil

| Player | O que faz | Tração | Flag |
|---|---|---|---|
| **Letrus** | Correção de **redação** por IA + trilha de escrita; vende como **política pública** para redes estaduais e SESI | Rede SESI: **+120 mil alunos** em 22 estados, **297,5 mil redações** corrigidas; ES: ~19 mil alunos / 178 escolas; presente em MT, GO, ES. Eleita pela **UNESCO** melhor tecnologia educacional | 🟢 |
| **Cria (Corretor de Redações por IA)** | Corrige redações dissertativas-argumentativas no padrão **ENEM** | **240 mil alunos**, ~**120 instituições** (públicas e privadas) | 🟢 |
| **Pod (Plataforma Otimizadora de Correção de Provas)** | Otimiza correção de provas; startup de engenheiros da **Poli/USP** | Piloto em 4 instituições (médio/superior) em SP | 🟢 |
| **Plataforma NEES (UFAL)** | Correção de textos a partir da avaliação do professor; **gratuita**, acadêmica | Pesquisa universitária | 🟢 |
| **Gomining** | IA para correção automática de produções textuais (graduação) | Comercial, nicho | 🟡 |
| **Soluções internas/AWS** | Escolas montando correção própria com LLMs (ex.: tutoriais AWS Brasil) | Pulverizado | 🟡 |

### Global

| Player | O que faz | Tração | Flag |
|---|---|---|---|
| **Gradescope (Turnitin)** | Correção multi-formato (manuscrito, provas, código), **answer grouping** por IA | **+140 mil instrutores** (Purdue, NYU…); parte da **Turnitin** | 🟢 |
| **EssayGrader** | Correção de redações em escala | **+100 mil professores**, **1.000+ escolas**; alega **93–95% de acurácia** vs humano | 🟢 |
| **CoGrader** | Correção integrada ao **Google Classroom** | Plano grátis até 100 submissões/mês; pago a partir de **US$19/mês** | 🟢 |
| **Turnitin Feedback Studio** | Integridade acadêmica + feedback | Padrão de mercado em universidades | 🟢 |
| **MagicSchool AI** | Suíte "tudo-em-um" para professores (planos + correção) | Grande base de professores nos EUA | 🟢 |

---

## Grupo 2 — Edtechs amplas (adjacentes/indiretos)

| Player | O que é | Tração / valuation | Flag |
|---|---|---|---|
| **Descomplica** | Cursinho/ENEM online → **faculdade digital** (graduação EAD), pós e cursos | ~**5 mi de alunos/mês** (plataforma+redes, 2021); **Série E de R$ 450 mi (~US$84 mi)** liderada por **SoftBank** e Invus (2021); **>US$100 mi** captados no total; mensalidade graduação R$150–200 | 🟢 |
| **Alura, Stoodi, Me Salva!, Árvore, etc.** | Conteúdo/cursos online | Players de conteúdo, não de correção | 🟡 |

> A Descomplica entrou em IA ("combo IA"), mas como **assistente de estudo**, não como corretor automático institucional. Concorre por orçamento de aluno/escola, não pelo mesmo job-to-be-done do NOVO CR.

---

## 2.1 Como são diferentes / parecidos com o NOVO CR

**Parecidos (job-to-be-done de correção):** Letrus, Cria, Pod, Gradescope, EssayGrader, CoGrader.
- Todos usam IA para **corrigir** e dar **feedback**, economizando tempo do professor.

**Diferenças-chave (oportunidade de posicionamento do NOVO CR):**

| Eixo | Concorrentes típicos | NOVO CR |
|---|---|---|
| **Escopo de correção** | Em geral **só redação/essay** (Letrus, Cria, EssayGrader) **ou** só múltipla escolha/manuscrito (Gradescope) | **Pipeline genérico** de provas/atividades, multi-questão, multimodelo |
| **Modelos de IA** | Modelo proprietário fechado, geralmente único | **Multi-provider** (OpenAI, Anthropic, Google) — flexibilidade e robustez |
| **Mercado** | Letrus/Cria fortes em **rede pública** (política pública); globais em universidades | A definir (privado/público/instituições BR) |
| **Idioma/contexto** | Globais são **inglês-first**; ENEM-specific (Cria) | Português-BR, mas arquitetura flexível |
| **Transparência do processo** | Caixa-preta na maioria | Pipeline por estágios + avisos/severidade (diferencial de confiança) |

**Semelhanças com Descomplica:** praticamente nenhuma no produto-núcleo — só o setor (edtech BR) e o público (estudantes/escolas).

## 2.2 Market share

- **Não há market share consolidado público** para "correção por IA" no Brasil (mercado nascente e fragmentado). 🟡
- Proxies de liderança no Brasil: **Letrus** (líder em redes públicas, escala estadual + SESI 120k+ alunos) e **Cria** (240k alunos). Esses são os players a vigiar.
- Global: **Gradescope/Turnitin** é o player dominante em ensino superior (140k+ instrutores); **EssayGrader** lidera em escala de professores individuais (100k+).
- **Tamanho do mercado (referência para o pleito):**
  - **Automated Essay Scoring**: ~**US$123 mi (2024)** → ~**US$345 mi (2033)**, CAGR ~12% (uma fonte); outra estima ~**US$0,43 bi (2026)** → **US$1,19 bi (2035)**. 🟢
  - **IA na Educação (guarda-chuva)**: ~**US$2,21 bi (2024)** → **US$5,82 bi (2030)**, CAGR ~17,5%. 🟢

> Leitura: o nicho específico de correção é pequeno e em rápido crescimento (12% a.a.); o guarda-chuva de IA-edu é grande e cresce ~17,5% a.a. Mercado ainda **sem dominante consolidado no Brasil** → janela de entrada.

## 2.3 Valor de mercado / valuation

| Player | Valor / sinal | Flag |
|---|---|---|
| **Descomplica** | Captou **R$ 450 mi (~US$84 mi)** Série E (SoftBank/Invus, 2021); **>US$100 mi** no total. Valuation não divulgado, mas no patamar de **centenas de milhões de USD** | 🟢/🟡 |
| **Turnitin (dona do Gradescope)** | Adquirida pela **Advance Publications** por ~**US$1,75 bilhão** (2019) — referência de valor da categoria | 🟢 |
| **Letrus** | Valuation **não público**; captou rodadas de venture/impacto (não divulgado na busca) | 🟡 |
| **EssayGrader / CoGrader** | Startups early-stage; valuation não público; CoGrader monetiza a **US$19/mês** | 🟡 |
| **Mercado AES** | ~**US$123 mi–US$430 mi** hoje, rumo a **~US$1+ bi** na próxima década | 🟢 |

> Valuations específicos de startups de correção por IA (Letrus, Cria, EssayGrader, CoGrader) **não são públicos**. O melhor proxy de "valor da categoria" é a aquisição da **Turnitin por ~US$1,75 bi** e o tamanho de mercado AES.

---

## Resumo do Bloco 2

- **Concorrente "igual" ≠ Descomplica.** Os diretos são **Letrus** e **Cria** (BR) e **Gradescope/EssayGrader/CoGrader** (global).
- **Market share:** sem dado consolidado; Letrus/Cria lideram no BR público; Gradescope/EssayGrader no global. Mercado AES ~US$123–430 mi, CAGR ~12%.
- **Valuation:** Descomplica >US$100 mi captados; Turnitin vendida por ~US$1,75 bi (proxy da categoria); startups de correção sem valuation público.
- **Diferencial do NOVO CR:** correção **genérica multi-questão + multi-provider + pipeline transparente em PT-BR** — versus concorrentes especializados só em redação ou só em manuscrito.

## Fontes

- [Letrus — site oficial](https://www.letrus.com/)
- [Portal da Indústria — IA corrige +297 mil redações na rede SESI (Letrus)](https://noticias.portaldaindustria.com.br/noticias/educacao/inteligencia-artificial-auxilia-correcao-de-mais-de-297-mil-redacoes-na-rede-sesi/)
- [SEDU-ES — plataforma de IA de redação (Letrus)](https://sedu.es.gov.br/Not%C3%ADcia/sedu-amplia-uso-de-plataforma-de-inteligencia-artificial-de-redacao-para-todo-ensino-medio)
- [PORVIR — startup ajuda a otimizar correção de provas (Pod / Cria)](https://porvir.org/startup-ajuda-otimizar-correcao-de-provas/)
- [NEES/UFAL — plataforma de correção de redações por IA](https://www.nees.ufal.br/plataforma-que-usa-inteligencia-artificial-auxilia-professores-na-correcao-de-redacoes/)
- [Exame — Descomplica capta R$ 450 milhões (Série E)](https://exame.com/pme/descomplica-recebe-aporte-de-r-450-milhoes-para-investir-em-faculdade-digital/)
- [Brazil Journal — Descomplica levanta US$ 84 milhões](https://braziljournal.com/descomplica-levanta-us-84-milhoes/)
- [Exame — estratégia da Faculdade Descomplica 2024 (combo IA)](https://exame.com/bussola/curso-novo-pos-ilimitada-e-combo-ia-a-estrategia-da-faculdade-descomplica-para-2024/)
- [Gradescope (Turnitin)](https://www.gradescope.com/)
- [Wise.live — Best AI Grading Tools 2026 (Gradescope, EssayGrader, CoGrader)](https://www.wise.live/blog/best-ai-grading-tools-for-teachers/)
- [CoGrader](https://cograder.com/)
- [Business Research Insights — Automated Essay Scoring Engine Market](https://www.businessresearchinsights.com/market-reports/automated-essay-scoring-engine-market-113581)
- [Verified Market Reports — Automated Essay Scoring Software Market](https://www.verifiedmarketreports.com/product/automated-essay-scoring-software-market/)
- [Grand View / Mordor — AI in Education Market](https://www.mordorintelligence.com/industry-reports/ai-in-education-market)
