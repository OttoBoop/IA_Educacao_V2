# Rio 3.0 -- Nota Tecnica de Provider e Plano de Testes

**Data:** 2026-04-17
**Responsavel:** Codex
**Status:** PAUSADO em 2026-04-28; pesquisa preservada para retomada depois do
saneamento dos documentos principais

---

## Resumo executivo

O `Rio 3.0` deixou de ser apenas um requisito futuro incerto. Ja existem fontes
publicas indicando que a Prefeitura/IplanRio lancou a familia `Rio 3 Open` em
abril de 2026, com pesos abertos no Hugging Face. A organizacao publica
`prefeitura-rio` lista 6 modelos relacionados:

- `prefeitura-rio/Rio-3.0-Open`
- `prefeitura-rio/Rio-3.0-Open-Search`
- `prefeitura-rio/Rio-3.0-Open-Mini`
- `prefeitura-rio/Rio-3.0-Open-Nano`
- `prefeitura-rio/Rio-2.5-Open`
- `prefeitura-rio/Rio-2.5-Open-VL`

Para o NOVO CR, o caminho mais pragmatico de teste e **Rio Open Mini via endpoint
OpenAI-compatible**. O nome canonico dos pesos no Hugging Face e
`prefeitura-rio/Rio-3.0-Open-Mini`, mas o alias real no endpoint com API key pode
ser diferente. Portanto, antes de rodar testes, o orquestrador deve descobrir os
IDs reais via `/v1/models` ou endpoint equivalente, sem expor a chave.

Escopo de teste travado: documentar todos os modelos possiveis, mas executar
testes apenas com **Rio Open Mini** quando o fluxo de chave estiver planejado,
seguro e operacional.

Estado aprovado em 2026-04-17: a execucao real da frente Rio 3 deve comecar
pelo site oficial no Render. A chave real entra pelo Render Dashboard ou por
secrets/env server-side equivalentes, nunca por chat, docs, logs, URL, preview
ou popup publico. Enquanto nao houver admin gate, autorizacao e CORS/origem
restritos para `/api/settings/*`, o popup publico segue bloqueado para segredo
real. A primeira validacao operacional e smoke de chat simples com JSON valido
em Rio Open Mini; Rio Open Mini e o unico alvo inicial. Nano permanece apenas
catalogado/documentado. Tool calling ainda nao esta validado.

Ponto critico: o pipeline do NOVO CR depende de **tool calling** para as etapas
`CORRIGIR`, `ANALISAR_HABILIDADES` e `GERAR_RELATORIO`. O codigo atual so
executa `chat_with_tools()` para `ProviderType.OPENAI`, `ANTHROPIC` e `GOOGLE`.
Logo, Rio 3.0 so sera um substituto real no pipeline se:

1. o endpoint usado suportar tools no formato OpenAI; ou
2. implementarmos fallback estruturado por JSON para modelos sem tool calling; ou
3. adicionarmos um provider especifico (`RIO3`) com estrategia propria.

---

## Fontes verificadas

### Fontes primarias ou quase primarias

1. Hugging Face -- `prefeitura-rio/Rio-3.0-Open-Mini`
   - URL: https://huggingface.co/prefeitura-rio/Rio-3.0-Open-Mini
   - Desenvolvedor declarado: IplanRIO.
   - Licenca: MIT.
   - Base model: `Qwen3-4B-Thinking-2507`.
   - Parametros: ~4B.
   - Context window: 262.144 tokens.
   - Max output padrao: 81.920 tokens.
   - Como rodar: inclui comandos para `vLLM` e `SGLang`.
   - Observacao: a pagina informa que o modelo nao esta hospedado por um
     inference provider oficial no Hugging Face.

2. Hugging Face -- `prefeitura-rio/Rio-3.0-Open`
   - URL: https://huggingface.co/prefeitura-rio/Rio-3.0-Open/tree/refs%2Fpr%2F1
   - README em `refs/pr/1`, nao necessariamente branch principal.
   - Licenca: MIT.
   - Base model: `Qwen3-235B-A22B-Thinking-2507`.
   - Arquitetura: MoE.
   - Parametros: ~235B total / ~22B ativos.
   - Context window: 262.144 tokens.
   - Peso no HF: ~470 GB.

3. Hugging Face -- `prefeitura-rio/Rio-3.0-Open-Nano`
   - URL: https://huggingface.co/prefeitura-rio/Rio-3.0-Open-Nano
   - Licenca: MIT.
   - Base tree indica Qwen3 1.7B.
   - README vazio no momento da verificacao.
   - Nao ha model card suficiente para inferir capacidades.

4. Hugging Face -- `prefeitura-rio/Rio-3.0-Open-Search`
   - URL: https://huggingface.co/prefeitura-rio/Rio-3.0-Open-Search
   - Licenca: MIT.
   - Pipeline: text generation.
   - Base model: `Qwen3-235B-A22B-Thinking-2507`.
   - Parametros: ~235B.
   - README vazio no momento da verificacao.
   - Hipotese: variante voltada a busca/search, mas sem model card suficiente
     para assumir API, ferramentas ou comportamento de retrieval.

5. Hugging Face -- `prefeitura-rio/Rio-2.5-Open`
   - URL: https://huggingface.co/prefeitura-rio/Rio-2.5-Open
   - Licenca: MIT.
   - Base model: `Qwen3-30B-A3B-Thinking-2507`.
   - Arquitetura: MoE.
   - Parametros: ~30B total / ~3B ativos.
   - Context window: 262.144 tokens.

6. Hugging Face -- `prefeitura-rio/Rio-2.5-Open-VL`
   - URL: https://huggingface.co/prefeitura-rio/Rio-2.5-Open-VL
   - Licenca: MIT.
   - Pipeline: image-text-to-text.
   - Base model: `Qwen3-VL-4B-Instruct`.
   - Parametros: ~4B.
   - README vazio no momento da verificacao.
   - E o unico modelo publico da familia com pipeline multimodal no HF, mas nao
     entra no primeiro teste Rio 3 do NOVO CR.

7. Rio.IA -- Secretaria Municipal de Ciencia e Tecnologia
   - URL: https://cienciaetecnologia.prefeitura.rio/rio-ia/
   - Confirma contexto institucional: hub de IA da cidade, coordenado pela SMCTI
     com ABDI e PUC-Rio/Instituto ECOA.
   - Importante: e uma fonte sobre o ecossistema Rio.IA, nao especificamente
     sobre os pesos do Rio 3.0.

### Fontes jornalisticas uteis

8. Mobile Time, 2026-04-02
   - URL: https://www.mobiletime.com.br/noticias/02/04/2026/prefeitura-do-rio-3-llms/
   - Reporta o lancamento de uma familia com seis LLMs: Rio 3.0 Open, Rio 3.0
     Open Mini, Rio 3.0 Open Nano, Rio 3.0 Search, Rio 2.5 Open e Rio 2.5 Open VL.
   - Reporta custo de desenvolvimento de R$ 500 mil e uso a partir de Qwen.
   - Reporta alegacao de ate 1 bilhao de tokens de janela de contexto e ate 30x
     menos custo em algumas aplicacoes.
   - Cuidado: ha uma divergencia com o model card do HF. A materia fala em
     `Open Mini` com 44B parametros, enquanto o Hugging Face declara 4B.

9. Featherless.ai -- endpoint terceiro para `Rio-3.0-Open-Mini`
   - URL: https://featherless.ai/models/prefeitura-rio/Rio-3.0-Open-Mini
   - Pode servir para smoke test remoto sem GPU propria.
   - Nao deve ser tratado como fonte de verdade de producao.

---

## Catalogo operacional de modelos Rio

Esta tabela separa o nome canonico publico dos pesos do possivel alias de API.
Os aliases do endpoint ainda precisam ser confirmados quando houver fluxo seguro
para a chave.

| Modelo publico | HF model ID canonico | Tipo | Base/tamanho publico | Status para NOVO CR |
| --- | --- | --- | --- | --- |
| Rio 3.0 Open | `prefeitura-rio/Rio-3.0-Open` | Texto | Qwen3-235B-A22B; ~235B/~22B ativos | Documentar; nao testar primeiro |
| Rio 3.0 Open Search | `prefeitura-rio/Rio-3.0-Open-Search` | Texto/search a confirmar | Qwen3-235B-A22B; ~235B | Documentar; nao testar primeiro |
| Rio Open Mini / Rio 3.0 Open Mini | `prefeitura-rio/Rio-3.0-Open-Mini` | Texto | Qwen3-4B-Thinking; ~4B | **Unico alvo de teste inicial** |
| Rio Open Nano / Rio 3.0 Open Nano | `prefeitura-rio/Rio-3.0-Open-Nano` | Texto | Qwen3-1.7B | Documentar; acesso informado pelo usuario; nao testar primeiro |
| Rio 2.5 Open | `prefeitura-rio/Rio-2.5-Open` | Texto | Qwen3-30B-A3B; ~30B/~3B ativos | Documentar; referencia comparativa |
| Rio 2.5 Open VL | `prefeitura-rio/Rio-2.5-Open-VL` | Multimodal | Qwen3-VL-4B-Instruct; ~4B | Documentar; possivel futuro OCR/vision |

Regras de nomenclatura para o projeto:

- usar `Rio Open Mini` como nome curto operacional quando falarmos do primeiro
  teste;
- usar o HF model ID completo somente quando estivermos falando dos pesos
  publicos ou de um servidor local que exponha exatamente esse ID;
- nao assumir que o endpoint com API key usa o mesmo `model` do Hugging Face;
- antes do primeiro teste com chave, consultar `/v1/models` ou endpoint
  equivalente e registrar o alias real retornado;
- se o endpoint retornar aliases como `rio-open-mini`, `rio-3-mini`,
  `rio-3.0-open-mini` ou variantes semelhantes, o teste deve usar o alias
  retornado pela API, nao o nome inferido do documento.

---

## O que ja podemos assumir

### 1. O melhor alvo inicial e Rio Open Mini

Motivos:

- tem model card completo;
- e leve o suficiente para teste local/terceirizado;
- tem instrucoes de `vLLM` e `SGLang`;
- e focado em raciocinio/matematica, que combina com correcao educacional;
- tem licenca MIT;
- tem suporte declarado a portugues e ingles.
- o usuario informou que ha acesso aos modelos Mini e Nano, e escolheu testar
  apenas o Mini primeiro.

### 2. Rio 3.0 Open completo nao e alvo inicial de teste

O `Rio-3.0-Open` tem ~470 GB em arquivos no Hugging Face e ~235B parametros.
Mesmo com MoE (~22B ativos), nao e adequado para uma primeira prova de conceito
local no ambiente atual.

### 3. Nano e promissor para custo, mas nao entra no primeiro teste

O `Rio-3.0-Open-Nano` aparece no Hugging Face, mas o README esta vazio. A materia
do Mobile Time o descreve como o modelo compacto da familia, mas ainda falta
confirmar:

- modelo base e tamanho exato;
- capacidade de seguir JSON;
- capacidade de tool calling;
- contexto e max output;
- qualidade em portugues educacional.

Mesmo com acesso ao Nano, ele deve ficar documentado e reservado para uma fase
posterior. O primeiro teste operacional continua restrito ao Rio Open Mini.

---

## Impacto no NOVO CR

### Chat simples

O NOVO CR ja consegue conversar com endpoints compativeis com OpenAI em:

- `backend/chat_service.py`
- `ChatClient._chat_openai()`
- `ChatClient._chat_openai_compatible()`
- `ProviderType.CUSTOM`
- `ProviderType.VLLM`
- `ProviderType.LMSTUDIO`

Porem ha uma diferenca pratica:

- se configurarmos Rio 3 como `VLLM`, hoje `chat()` cai no fallback `CUSTOM` ou
  nao recebe tratamento completo em todos os fluxos;
- se configurarmos como `OPENAI` com `base_url` customizada, o `chat_with_tools`
  tambem usa o caminho OpenAI, o que e desejavel para testar tool calling;
- para vLLM local, pode ser necessario aceitar uma API key dummy ou corrigir o
  gate que exige API key para tudo exceto Ollama.

### Pipeline com tools

O gargalo esta aqui. `ChatClient.chat_with_tools()` so dispatcha tools para:

- `ProviderType.ANTHROPIC`
- `ProviderType.OPENAI`
- `ProviderType.GOOGLE`

Qualquer outro tipo cai em chat simples, sem tools. Isso significa que Rio 3 nao
deve ser considerado "pipeline-ready" ate validarmos:

1. se o endpoint OpenAI-compatible retorna `tool_calls`;
2. se o modelo sabe escolher `create_document` corretamente;
3. se ele gera `content` JSON valido dentro da tool;
4. se preserva `_avisos_documento`, `_avisos_questao` e `_avisos_stage`;
5. se nao cria documentos fantasma em caso de falha;
6. se tokens sao contabilizados separadamente ou ao menos totalizados.

### Multimodal/PDF

O pipeline usa multimodal para as etapas `EXTRAIR_*`. Os model cards do Rio 3
Open e Mini sao de text generation. O Rio 2.5 Open VL e citado publicamente como
modelo de visao, OCR e grounding, mas ainda precisa de fonte tecnica/model card.

Conclusao: Rio 3.0 Open Mini deve ser testado primeiro nas etapas tool-use
textuais (`CORRIGIR`, `ANALISAR_HABILIDADES`, `GERAR_RELATORIO`), nao nas etapas
multimodais (`EXTRAIR_QUESTOES`, `EXTRAIR_GABARITO`, `EXTRAIR_RESPOSTAS`).

---

## Plano de testes proposto

Escopo travado: os testes operacionais desta frente devem rodar apenas com
**Rio Open Mini**. Os demais modelos ficam catalogados para decisao futura.

### Fase 0 -- Confirmar endpoint

Objetivo: saber onde o Rio Open Mini sera testado:

1. `vLLM` local;
2. `SGLang` local;
3. Featherless/terceiro;
4. portal `ai.rio`, se expuser API;
5. outro endpoint interno da Prefeitura/IplanRio.

Antes de qualquer chamada de teste com chave:

- configurar a chave pelo fluxo seguro do site/sistema, nao pelo chat;
- chamar `/v1/models` ou equivalente;
- registrar no documento o alias real do Rio Open Mini retornado pelo endpoint;
- confirmar que Nano aparece apenas como disponivel/documentado, nao selecionado
  para a bateria inicial.

Comando base esperado para vLLM:

```bash
vllm serve prefeitura-rio/Rio-3.0-Open-Mini \
  --tensor-parallel-size 1 \
  --max-model-len 32768 \
  --trust-remote-code
```

Observacao: o model card sugere 262.144 tokens, mas para teste local inicial
e mais realista limitar para 32k se a GPU/memoria for modesta.

### Fase 1 -- Smoke test de chat

Teste manual:

```bash
curl "$RIO3_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $RIO3_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "$RIO_OPEN_MINI_MODEL_ID",
    "messages": [
      {"role": "system", "content": "Responda apenas em JSON valido."},
      {"role": "user", "content": "Corrija: 2+2=5. Retorne {\"ok\":false,\"comentario\":\"...\"}."}
    ],
    "temperature": 0.2,
    "max_tokens": 512
  }'
```

`RIO_OPEN_MINI_MODEL_ID` deve ser preenchido com o alias real retornado pelo
endpoint. Em servidor local vLLM, pode ser
`prefeitura-rio/Rio-3.0-Open-Mini`; em endpoint hospedado, pode ser outro nome.

Aceite:

- HTTP 200;
- resposta em JSON parseavel;
- resposta em portugues;
- sem raciocinio exposto desnecessario.

### Fase 2 -- Tool calling minimo

Enviar uma tool fake estilo OpenAI somente para Rio Open Mini:

```json
{
  "type": "function",
  "function": {
    "name": "create_document",
    "description": "Cria um documento JSON",
    "parameters": {
      "type": "object",
      "properties": {
        "filename": {"type": "string"},
        "content": {"type": "string"}
      },
      "required": ["filename", "content"]
    }
  }
}
```

Aceite:

- `finish_reason == "tool_calls"`;
- existe `message.tool_calls`;
- argumentos sao JSON valido;
- `content` contem JSON valido do documento.

Se falhar, Rio 3.0 ainda pode ser usado para chat simples, mas nao para o Path 2
do pipeline sem refatorar o executor para "structured JSON without tools".

### Fase 3 -- Teste controlado no NOVO CR

Criar modelo temporario no `models.json` com:

- `tipo`: preferencialmente `openai` para testar o caminho de tools;
- `nome`: `Rio Open Mini (teste)`;
- `modelo`: alias real do Rio Open Mini exposto pelo endpoint;
- `base_url`: endpoint OpenAI-compatible;
- `suporta_function_calling`: `true` somente se a Fase 2 passou;
- `suporta_vision`: `false`;
- `suporta_temperature`: `true`;
- `max_tokens`: comecar baixo (4096-8192) para nao travar teste.

Rodar uma atividade pequena com um aluno ja auditado. Nao usar como default.
Nao rodar Nano, Open completo, Search, 2.5 Open ou 2.5 Open VL nesta bateria.

### Fase 4 -- Comparacao

Comparar Rio Open Mini contra:

- Claude Haiku 4.5 (default atual);
- Gemini 3 Flash;
- GPT-5 Nano;
- GPT-4o ou GPT-5 Mini, se custo permitir.

Metricas:

- taxa de JSON valido;
- taxa de tool call correta;
- latencia por etapa;
- tokens totais;
- custo estimado;
- qualidade pedagogica da correcao;
- preservacao de `_avisos_*`;
- criacao de documentos fantasma;
- aderencia ao schema final.

---

## Mudancas de codigo provavelmente necessarias

### Curto prazo

1. Permitir API key dummy para `VLLM`, `LMSTUDIO` e talvez `CUSTOM` local.
2. Permitir `chat_with_tools()` para endpoints OpenAI-compatible, nao apenas
   `ProviderType.OPENAI`.
3. Adicionar teste unitario para garantir que `ProviderType.VLLM` com
   `suporta_function_calling=True` nao cai em chat simples.
4. Adicionar `input_tokens` e `output_tokens` ao retorno de OpenAI-compatible,
   quando o endpoint fornecer `usage.prompt_tokens` e `usage.completion_tokens`.

### Medio prazo

1. Adicionar provider `RIO3` se o portal `ai.rio` tiver autenticacao ou payload
   proprio.
2. Adicionar entradas no `model_catalog.json` para `rio3-open-mini`,
   `rio3-open`, `rio3-open-search`, `rio3-open-nano`, `rio2.5-open` e
   `rio2.5-open-vl`, mantendo Rio Open Mini como unico alvo de teste inicial.
3. Criar suite `test_rio3_provider.py` com testes de:
   - chat simples;
   - JSON schema;
   - tool calling;
   - pipeline dry-run;
   - fallback sem tools.

---

## Orquestracao Rio 3

Esta secao registra a governanca combinada para a frente Rio 3.0. Ela nao
autoriza implementacao automatica nem acionamento automatico de subagentes.
Atualizacao operacional de 2026-04-17: quando o usuario delegar explicitamente
o papel de orquestrador, Paulo pode acionar subagentes de diagnostico/leitura
com escopo fechado e relatorio continuo. Acoes com segredo, deploy, push, hook
ou mudanca publica seguem exigindo autorizacao explicita.

### Decisoes travadas

- O papel do orquestrador, nesta fase, e **planejar e documentar**.
- Subagentes serao aprovados **um por um** antes de serem acionados.
- Rio 3 entra primeiro como **preset custom/OpenAI-compatible**, nao como
  provider dedicado.
- A chave Rio 3 nao deve ser colada em conversa. O fluxo planejado e: o usuario
  informa a chave pelo site ou por outro caminho seguro definido pelo agente; o
  sistema guarda no cofre existente; o orquestrador verifica disponibilidade,
  mascaramento e teste de conexao, sem revelar o segredo.

### Protocolo de aprovacao de subagentes

Nenhum subagente deve ser acionado sem uma proposta previa para revisao humana.
A proposta deve conter:

- nome de trabalho do agente;
- objetivo geral;
- constraints obrigatorias;
- entradas permitidas;
- saida esperada;
- limite explicito de escopo;
- confirmacao de que o agente nao implementara nada sem nova aprovacao.

O plano dos subagentes deve ser intencionalmente objetivo e orientado por
missao. O orquestrador define o problema, as constraints e o plano de longo
prazo; o subagente pode propor a solucao tecnica e a divisao de testes.

### Protocolo para chave Rio 3

O orquestrador nunca deve pedir para o usuario colar a chave Rio 3 no chat,
em documentos, em saidas de terminal ou em logs. A responsabilidade do
orquestrador e conduzir o usuario ate um fluxo seguro no site/sistema e depois
verificar apenas sinais seguros:

- existencia de uma key cadastrada;
- provider/empresa correta;
- preview mascarado, nunca valor completo;
- teste de conexao sem ecoar o segredo;
- modelo Rio 3 configurado para usar a key sem expor seu valor.

O valor completo da chave deve permanecer server-side. O frontend pode exibir
somente `api_key_preview` ou status equivalente. Qualquer fluxo que mostre a
chave inteira de volta ao navegador deve ser tratado como defeito de seguranca.

"Estar apto a receber a chave" significa estar apto a orientar e validar o
fluxo seguro de cadastro no site/sistema. Nao significa receber a chave em texto
livre na conversa.

### Estado atual descoberto

O projeto ja possui pecas importantes para esse fluxo:

- `ApiKeyManager` com criptografia Fernet e persistencia em
  `backend/data/api_keys.json`;
- arquivo de chave Fernet em `backend/data/.encryption_key`;
- `api_keys.json` e `.encryption_key` ignorados pelo Git;
- endpoints de settings para criar, listar, atualizar e remover API keys;
- modal de API Keys no site;
- cadastro de modelo customizado com `base_url`, `custom_model_id`,
  `max_tokens` e `temperature`;
- botao de teste de modelo.

Logo, a diretriz inicial e reaproveitar o cofre existente sempre que ele for
seguro o suficiente para o ambiente de deploy.

### Risco atual conhecido

A auditoria rapida do codigo indica que o app nao parece ter autenticacao/admin
gate nas rotas de settings, e o CORS esta aberto. Isso pode ser aceitavel em
ambiente local ou servidor privado controlado, mas deve ser tratado como
bloqueador se a interface estiver publica ou multiusuario.

Antes de aceitar gestao de chaves por uma URL publica, um agente deve propor no
minimo:

- protecao de acesso para rotas e UI de settings;
- regra clara de quem pode cadastrar/remover chaves;
- garantia de que a chave nunca aparece completa em resposta HTTP;
- estrategia para evitar vazamento em logs de erro;
- teste de regressao para mascaramento e persistencia criptografada.

### Primeiro subagente proposto

**Nome de trabalho:** Agente Cofre Rio 3.

**Objetivo geral:** descobrir um jeito seguro e pratico para o usuario fornecer
a chave Rio 3 ao sistema existente do site, para que ela fique guardada de forma
segura e utilizavel por todos os fluxos do NOVO CR.

**Constraints:**

- nao pedir nem registrar a chave em chat, logs, docs ou saida de terminal;
- reaproveitar o sistema existente sempre que seguro: `ApiKeyManager`, modal de
  API Keys, endpoints de settings e cadastro customizado;
- garantir que o frontend nunca receba a chave completa de volta, apenas preview
  mascarado;
- considerar que o modelo sera OpenAI-compatible/custom preset na primeira
  versao;
- se o ambiente for publico ou multiusuario, apontar claramente quais protecoes
  minimas faltam antes de aceitar gestao de chave pelo site;
- nao implementar nada sem nova aprovacao.

**Entradas permitidas:**

- codigo fonte do backend e frontend;
- docs de planejamento Rio 3;
- configuracoes de Git ignore;
- estrutura de testes existente;
- descricao do plano de longo prazo.

**Entradas proibidas:**

- valor real da chave Rio 3;
- qualquer segredo de API em claro;
- alteracoes de codigo sem aprovacao posterior.

**Saida esperada:**

- diagnostico curto do fluxo atual;
- proposta de solucao para entrada, armazenamento e verificacao da chave;
- lista de riscos e mitigacoes;
- lista de testes importantes, sem precisar escrever os testes ainda;
- arquivos provaveis a tocar, com justificativa.

### Resultado do Agente Cofre Rio 3

Rodada executada em 2026-04-17. Diagnostico principal:

- o cofre ja existe e salva API keys com Fernet;
- a listagem retorna apenas `api_key_preview`;
- o modelo ja tem campo `api_key_id`;
- o fluxo de endpoint customizado nao expunha `api_key_id` no frontend nem no
  payload especifico de `/api/settings/models/custom`;
- sem vinculo explicito, Rio Open Mini poderia cair em fallback de chave por
  empresa e usar a chave errada.

Decisao tecnica da primeira implementacao:

- cadastrar a chave Rio como `Custom/Rio 3` no cofre existente;
- criar o endpoint Rio Open Mini como OpenAI-compatible/custom endpoint;
- selecionar explicitamente a chave cadastrada no formulario customizado;
- persistir `api_key_id` no modelo;
- manter tool calling desligado ate o smoke test especifico passar.

Arquivos alterados nesta rodada:

- `backend/routes_chat.py`: `CustomModelCreate` aceita `api_key_id`, valida se a
  key existe e persiste o vinculo no modelo customizado;
- `frontend/index_v2.html`: modal de API key ganhou opcao `Custom/Rio 3`, e a aba
  Customizado ganhou seletor de API key que envia `api_key_id`; tambem ganhou a
  entrada segura `?setup=rio3-key`, que abre o popup de cadastro de chave ja com
  `Custom/Rio 3` selecionado;
- `backend/tests/unit/test_rio3_key_flow.py`: testes focados para criptografia,
  mascaramento, persistencia de `api_key_id`, popup seguro e wiring da UI.

Entrada segura pronta para a chave:

```bash
xdg-open 'http://127.0.0.1:8000/?setup=rio3-key'
```

Esse comando nao transporta a chave pela URL. Ele apenas abre o site local no
popup de API key, com `Custom/Rio 3` selecionado e aviso explicito para colar a
chave somente no cofre do site.

Producao no site real:

- o popup local serve para desenvolvimento e para evitar chave no chat;
- no Render, a chave Rio 3 deve entrar primeiro como secret de ambiente, nao pelo
  navegador publico;
- variaveis planejadas/declaradas no blueprint: `RIO3_API_KEY`,
  `RIO3_BASE_URL`, `RIO3_MODEL_ID`, `RIO3_MAX_TOKENS`, `RIO3_TEMPERATURE`;
- quando `RIO3_API_KEY`, `RIO3_BASE_URL` e `RIO3_MODEL_ID` estiverem presentes,
  o backend cria/sincroniza uma API key `Custom/Rio 3` criptografada e um modelo
  `Rio Open Mini (env)` com `suporta_function_calling=false`;
- a URL publica do popup so deve ser usada para chave real depois de existir
  auth/admin gate para `/api/settings/*` ou outro secret store persistente.

Limite ainda ativo:

- se a interface estiver publica ou multiusuario, ainda falta auth/admin gate
  antes de considerar gestao de segredo segura em producao;
- a chave real continua proibida em chat, docs, logs e saidas de terminal;
- os testes de modelo devem esperar o cadastro seguro da chave e a descoberta do
  alias real do Rio Open Mini via `/v1/models` ou equivalente.

### Interfaces e comportamentos esperados

O plano de implementacao futuro deve preservar ou evoluir estas interfaces:

- API keys continuam server-side, criptografadas, e retornam apenas
  `api_key_preview`;
- o site deve ter uma forma clara de cadastrar uma chave Rio 3 ou chave de
  endpoint compativel;
- todos os modelos Rio conhecidos devem poder ser documentados/catalogados, mas
  a primeira bateria de teste so pode selecionar Rio Open Mini;
- o modelo Rio Open Mini deve poder ser cadastrado como endpoint
  custom/OpenAI-compatible com `base_url`, `model_id`, `max_tokens` e capacidade
  de tools somente depois de validacao;
- o botao de testar modelo deve confirmar conexao sem expor segredo;
- usuarios podem usar o modelo configurado, mas nao podem ler a chave.

### Testes a definir por subagentes

A prioridade exata da suite fica para o agente autorizado propor. A cobertura
minima esperada inclui:

- a chave salva nao aparece em plaintext no arquivo persistido;
- a API de listagem retorna preview mascarado, nunca o segredo inteiro;
- o fluxo de cadastro Rio 3 aceita endpoint custom/OpenAI-compatible;
- o teste de conexao usa a chave armazenada sem expor valor em resposta, toast
  ou logs;
- um modelo Rio 3 sem tool calling validado nao pode ser marcado como pronto
  para pipeline;
- se tool calling for habilitado, deve haver teste especifico provando que nao
  cai em chat simples.

### Assumptions operacionais

- Este documento e a fonte de planejamento para a frente Rio 3 nesta fase.
- Nenhum subagente sera acionado automaticamente.
- A primeira proposta de subagente sera ampla e orientada por objetivo,
  deixando o agente propor a solucao dentro das constraints.
- O plano tecnico final de testes fica para depois que o primeiro agente
  entregar a proposta dele.
- Este documento e a nota tecnica. O estado vivo, datado, de bloqueios,
  decisoes e handoffs da frente Rio 3 deve ser espelhado em
  `09_progresso_longo_prazo.md` antes de prosseguir para deploy, teste real ou
  mudanca de criterio.

### Reorientacao do orquestrador Paulo -- site oficial

Registro de 2026-04-17: a frente Rio 3 travou porque o fluxo local de popup foi
tratado como se resolvesse o problema do site oficial. Isso esta incorreto. O
orquestrador Paulo deve considerar "pronto para receber chave" apenas quando o
caminho estiver adequado ao ambiente oficial do NOVO CR.

Decisao corrigida:

- solucoes locais so podem ser usadas para desenvolvimento ou verificacao
  controlada;
- para o site oficial Render, a chave real deve entrar primeiro por secret de
  ambiente (`RIO3_API_KEY`) ou por painel administrativo autenticado;
- enquanto `/api/settings/*` estiver publico e sem admin gate, popup publico de
  chave fica bloqueado;
- o plano de longo prazo deve registrar cada mudanca relevante de estado, nao
  apenas a nota tecnica Rio 3.

Subagentes acionados nesta reorientacao:

- **Agente Planejador Rio 3 (Maxwell):** revisou os Docs 05, 08 e 09 e confirmou
  que o conflito central e `dev-only` versus entrega no site oficial;
- **Agente Seguranca Site Oficial (Hume):** auditou settings, CORS e Render, e
  confirmou que o caminho seguro de producao e secret de deploy + admin gate
  antes de qualquer popup publico;
- **Agente Registro Longo Prazo (Schrodinger):** criado para manter
  `09_progresso_longo_prazo.md` atualizado sempre que houver mudanca relevante
  de estado, decisao ou bloqueio no roadmap.

Subagentes acionados na rodada de orquestracao oficial:

- **Agente Integracao Render Rio 3 (Nietzsche):** confirmou que a chave real
  deve entrar por secrets do Render e que `render.yaml` precisava declarar
  `RIO3_API_KEY`, `RIO3_BASE_URL`, `RIO3_MODEL_ID`, `RIO3_MAX_TOKENS` e
  `RIO3_TEMPERATURE`;
- **Agente Auditor Conflitos Workspace (Sagan):** encontrou uma sessao externa
  `claude --resume b88b53bf-ffe7-498c-88eb-8a79de268557` ativa e recomendou
  edicoes pequenas/datadas em docs compartilhados, sem tocar nas frentes
  sensiveis de backend;
- **Agente Documentador Rio 3 Oficial (Gauss):** revisou Docs 05, 08 e 09 e
  pediu consolidacao explicita de estado atual, bloqueio do site oficial, fluxo
  da chave, agentes externos e proximos passos.

Regra de orquestracao: todo novo passo que altere status de Rio 3, site oficial,
deploy, chave de API, endpoint real, ou criterios de teste deve atualizar o
registro de progresso de longo prazo na mesma rodada.

Durante execucao de subagentes, Paulo deve emitir relatorios curtos de
monitoramento com:

- status de cada agente;
- decisao ou arquivo que ele esta investigando;
- impacto parcial no plano Rio 3;
- pergunta que ficou bloqueada, se houver.

Esses relatorios nao substituem o registro final em `09_progresso_longo_prazo.md`;
eles servem para manter o usuario orientado enquanto a orquestra trabalha.

Paulo tambem deve monitorar agentes/processos externos que nao foram criados por
ele. Como esses agentes podem editar os mesmos documentos, Paulo deve:

- descobrir agentes externos por sinais locais antes de perguntar ao usuario:
  processos `codex`/`claude`, `/tmp/claude-*`, `subagents/*.jsonl`, timestamps
  recentes, `git status` e diffs por arquivo;
- conferir `git status`/trechos atuais antes de mexer nos `.md` compartilhados;
- tratar mudancas de autoria incerta como trabalho valido ate prova em contrario;
- nao sobrescrever consolidacoes recentes sem reler e explicar o motivo;
- avisar o usuario quando detectar mudancas paralelas em docs, backend ou
  configuracao que alterem a decisao Rio 3;
- perguntar antes de resolver conflitos narrativos entre registros de agentes.

### Informacoes que Paulo deve solicitar ao usuario

Para o usuario conseguir ajudar a orquestra sem expor segredo, Paulo deve pedir
apenas informacoes operacionais e confirmacoes de acao:

- prioridade da proxima etapa: deploy do suporte `RIO3_*` no Render ou admin
  gate antes de qualquer mudanca publica;
- URL base oficial do endpoint Rio, se ela puder ser compartilhada sem segredo;
- como descobrir o alias real do Rio Open Mini (`/v1/models`, painel do
  fornecedor, documentacao privada ou outro caminho);
- confirmacao de que `RIO3_API_KEY` foi configurada no Render, sem enviar o
  valor;
- aprovacao explicita antes de qualquer deploy, push ou acionamento de hook;
- regra de administracao: quem pode gerenciar modelos e chaves no site oficial.
- governanca do site oficial: quem administra modelos/chaves, se existe admin
  gate, e se a URL publica continua proibida para chaves reais ate autenticacao,
  autorizacao e CORS/origem estarem resolvidos.

Paulo nao deve pedir: valor da chave, print contendo segredo, logs com headers,
ou qualquer resposta de API que inclua token bruto.

---

## Lacunas em aberto

1. O portal `ai.rio` expoe API publica ou apenas interface/portal?
2. Existe API key oficial para orgaos publicos?
3. O endpoint oficial e OpenAI-compatible?
4. Ha suporte real a `tools`/function calling?
5. Ha suporte a JSON mode?
6. Ha modelo de visao oficial (`Rio 2.5 Open VL`) com endpoint e model card?
7. Quais sao limites reais de contexto, output, rate limit e concorrencia?
8. Quais dados foram usados no treinamento/fine-tuning e quais restricoes de
   privacidade/governanca se aplicam?
9. O uso em producao governamental exige rodar localmente ou pode usar endpoint
   hospedado?
10. Como citar corretamente as variantes: `Rio 3`, `Rio 3.0`, `Rio 3 Open`,
    `Rio 3.0 Open Mini`?

---

## Decisao recomendada

Assumir Rio 3.0 como uma frente propria do projeto, mas com escopo claro:

1. **Primeiro objetivo:** provar chat simples + JSON estruturado com Rio 3.0 Open
   Mini.
2. **Segundo objetivo:** provar ou negar tool calling.
3. **Terceiro objetivo:** se tool calling funcionar, testar `CORRIGIR` em um
   aluno pequeno e comparar com Haiku/Gemini/GPT.
4. **Nao usar Rio 3.0 no multimodal ainda.**
5. **Nao colocar como default ate passar nas metricas de schema, documentos e
   avisos.**
