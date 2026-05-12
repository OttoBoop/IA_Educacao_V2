# Plano Curto Paulo - Rio 3 no Render

**Data:** 2026-04-17
**Responsavel operacional:** Paulo
**Status:** PAUSADO em 2026-04-28 por decisao do usuario; foco atual e saneamento
dos documentos da pipeline

---

## Objetivo

Levar o Rio 3 do estado "catalogado" para o primeiro smoke operacional seguro no
site oficial Render, sem expor segredo em chat, docs, logs, frontend ou backend.

Pausa atual: este plano fica guardado, mas Paulo nao deve pedir chave, rodar
smoke, acionar deploy Rio ou convocar agentes Rio enquanto a reorganizacao dos
documentos estiver em andamento.

O plano curto nao tenta validar toda a familia Rio. Ele existe para responder uma
pergunta objetiva: o NOVO CR consegue chamar o endpoint Rio Open Mini, com chave
guardada no Render, e receber uma resposta minima sem vazar credenciais?

---

## Papel do Paulo

Paulo e o orquestrador da frente Rio 3. Ele nao deve ser apenas mensageiro entre
agentes: deve manter o quadro vivo, separar fatos de inferencias, perceber
bloqueios entre GitHub e Render, e pedir decisao humana quando faltar permissao
ou informacao segura.

Responsabilidades diretas:

- manter este plano curto como referencia operacional;
- acompanhar subagentes e registrar resultados relevantes no Doc 09;
- impedir que segredo, deploy hook, token ou preview de chave seja registrado;
- coordenar o loop GitHub -> Render -> smoke -> registro;
- manter Rio Open Mini como unico alvo de teste inicial;
- manter Nano apenas documentado ate haver decisao explicita para nova fase.

---

## Subagentes

Paulo pode acionar subagentes, mas cada um deve receber objetivo, entradas
permitidas, limites de arquivo e saida esperada.

Subagentes previstos:

- **GitHub/Deploy:** confirma branch, commit-alvo, PR/push quando autorizado, e
  estado de checks sem colar tokens ou hooks.
- **Render Ops:** orienta o usuario no Render Dashboard e verifica apenas sinais
  seguros de deploy e ambiente, sem pedir ou registrar valor da chave.
- **Smoke Rio:** executa o harness seguro depois que `RIO3_*` existir no Render e
  registra somente status, codigo de erro seguro e metadados nao sensiveis.
- **Documentacao:** atualiza Doc 09 e docs de plano com blocos datados pequenos.
- **Seguranca:** revisa se alguma rota, log ou doc exibiu segredo, preview de
  chave, URL de deploy hook, token ou header sensivel.

Nenhum subagente deve testar Nano, mudar frontend/backend ou criar fluxo publico
de chave real sem nova autorizacao.

---

## Fluxo Seguro no Render Dashboard

O cadastro da chave deve acontecer no site oficial Render, em variaveis de
ambiente server-side. O valor nunca deve passar pelo chat nem por documento.

Passos operacionais:

1. Paulo confirma qual servico Render esta em uso e qual commit/deploy esta live.
2. O usuario abre o Render Dashboard com a propria sessao.
3. O usuario cadastra `RIO3_API_KEY` no ambiente do servico.
4. O usuario cadastra tambem `RIO3_BASE_URL` e `RIO3_MODEL_ID`, quando esses
   valores forem conhecidos pelo endpoint oficial.
5. O usuario informa apenas "configurado" ou "nao configurado".
6. Paulo solicita deploy/redeploy somente quando houver permissao explicita.
7. Smoke Rio roda sem imprimir segredo, header de autorizacao, deploy hook ou
   preview da chave.

Se o alias do modelo ainda nao estiver confirmado, o caminho seguro e consultar
`/v1/models` ou equivalente pelo harness, registrando apenas o ID de modelo
necessario e nenhum header sensivel.

---

## Escopo de Modelo

### Unico alvo de teste inicial

O primeiro teste operacional deve usar somente **Rio Open Mini**.

Motivos:

- e o alvo aprovado para reduzir variaveis;
- e o modelo mais pragmatico para smoke inicial;
- permite validar secret, endpoint e formato OpenAI-compatible antes de discutir
  qualidade ou custo;
- evita misturar problemas de provisionamento com comparacao entre modelos.

### Nano

Rio Open Nano fica documentado, mas fora da primeira bateria. Ter acesso ao Nano
nao autoriza teste automatico. Qualquer mudanca de escopo precisa virar decisao
registrada antes.

---

## Loop GitHub / Render

O loop operacional deve ser curto e auditavel:

1. Confirmar estado local e `origin/main`.
2. Confirmar se ha commit aprovado para deploy.
3. Confirmar se GitHub Actions recentes existem e se estao verdes, quando
   aplicavel.
4. Confirmar estado do deploy live no Render.
5. Garantir que `RIO3_*` esta provisionado no Render, sem expor valores.
6. Acionar deploy/redeploy apenas com autorizacao.
7. Rodar smoke seguro contra o Render.
8. Registrar resultado no Doc 09 com data, commit observado, deploy observado e
   proximo bloqueio.

Estado conhecido para este recorte de plano:

- local/origin `main`: `50935ea`;
- Render live: `2e1098f`;
- GitHub Actions recentes: nenhuma execucao recente conhecida;
- ambiente local: sem `RENDER_API_KEY` e sem `RIO3_*`;
- smoke Rio: aguardando `RIO3_*` no Render.

Se outro agente avancar commit, deploy ou configuracao enquanto Paulo trabalha,
Paulo deve registrar a divergencia como novo fato datado antes de tomar decisao.

---

## Testes e Aceite

### Smoke minimo

O primeiro aceite nao e qualidade pedagogica. O aceite minimo e conectividade
segura:

- `RIO3_API_KEY`, `RIO3_BASE_URL` e `RIO3_MODEL_ID` existem no Render;
- deploy live recebeu as variaveis;
- harness Rio roda sem depender de segredo local;
- chamada a `/models` ou equivalente confirma o alias do Rio Open Mini;
- chamada simples de chat/completions retorna resposta sem tool calling;
- logs nao exibem segredo, token, deploy hook, header sensivel ou preview de
  chave.

### Aceite para seguir adiante

Depois do smoke minimo, Paulo pode propor a proxima fase apenas se:

- o resultado estiver registrado no Doc 09;
- o modelo testado for Rio Open Mini;
- Nano continuar fora do escopo;
- falhas estiverem classificadas como provisionamento, endpoint, auth, formato,
  timeout ou compatibilidade;
- qualquer teste de tool calling ficar explicitamente pendente ate nova decisao.

---

## Bloqueios Atuais

- `RIO3_*` ainda precisa existir no Render para smoke real.
- Sem `RENDER_API_KEY` local, Paulo nao deve tentar automacao direta do Render.
- Live Render conhecido ainda esta em commit anterior ao estado local/origin
  registrado para este plano.
- Sem GitHub Actions recentes conhecidas para usar como gate automatico.
- Admin gate da UI publica continua requisito antes de qualquer chave real por
  formulario publico.

---

## Historico: Enquanto a chave nao entra

Este bloco fica preservado como historico. Durante a pausa decidida em
2026-04-28, Paulo nao deve pedir chave Rio 3. Quando a frente for retomada, a
regra volta a ser: o plano curto nao deve ficar parado aguardando input de
segredo. Enquanto `RIO3_*` nao existir no Render, Paulo continua trabalhando no
caminho oficial:

- manter Doc 09 coerente com a matriz real de providers e com o estado do Render;
- separar o que e lote serio de deploy do que e artefato lateral no workspace;
- manter o saneamento do deploy hook e a regra de rotacao como precondicao de
  deploy manual;
- distinguir claramente bloqueio de segredo, bloqueio de ambiente local e
  bloqueio de produto/governanca;
- impedir que a frente Rio 3 apague o objetivo maior: pipeline oficial confiavel
  e verificado no site live.

---

## Registro de Execucao - 2026-04-17

- Subagentes concluidos: Saulo (Registro), Docs Rio 3 e Seguranca GitHub/Render.
- Paulo abriu a pagina de Environment do servico oficial no Render para cadastro
  manual de `RIO3_API_KEY`; nenhum segredo foi recebido no chat, terminal ou doc.
- Doc 11 foi saneado: deploy hook e service id expostos foram substituidos por
  placeholders, e a rotacao do hook ficou registrada como obrigatoria antes de
  qualquer uso.
- Verificacoes realizadas sem segredo: varredura de hook antigo e query string secreta,
  `py_compile` de arquivos Rio, e `git diff --check` do lote documental/codigo.
- Teste focado Rio 3 nao rodou por falta de dependencias Python locais
  (`pytest`, `httpx`, `cryptography`, `fastapi`); isso e bloqueio de ambiente,
  nao resultado funcional do Rio Open Mini.
- Commit, push, deploy hook e smoke real continuam bloqueados ate autorizacao
  explicita e ate `RIO3_*` existir no Render.

---

## Registro de Execucao - 2026-04-28

- Estado atualizado do branch oficial: local e `origin/main` em `479b77d`; o
  site live segue em `2e1098f`, portanto o gargalo de deploy oficial continua
  aberto.
- Triagem GitHub feita no repo oficial `OttoBoop/IA_Educacao_V2`:
  - branch padrao confirmada como `main`;
  - sem GitHub Actions recentes no recorte observado;
  - existe um PR antigo aberto (`#19`, branch
    `codex/create-prs-to-stabilize-prova-ai-v2`), mas ele nao representa o lote
    serio local em `main`.
- Verificacao live sem segredo:
  - `/api/health` segue saudavel;
  - `/api/settings/models` responde no shape `models + total`, com 13 modelos e
    nenhum Rio;
  - `/api/settings/api-keys` responde no shape `api_keys + total`, com 3 chaves
    env (`openai`, `anthropic`, `google`) e nenhuma `custom`/Rio.
- O bloqueio local de dependencias foi resolvido para verificacao: em venv
  temporario fora do repo, `pytest tests/unit/test_rio3_key_flow.py -q` passou
  com `12 passed`.
- Mitigacao de seguranca aplicada antes de qualquer deploy publico:
  - endpoints remotos customizados ficaram bloqueados fora de localhost, exceto
    no caso explicitamente autorizado do Rio 3 server-side;
  - o seletor de chaves do endpoint customizado passou a listar apenas keys
    `custom`, e o deep-link `?setup=rio3-key` ficou restrito a host local.
- Lote serio staged para o proximo gate:
  - `backend/chat_service.py`
  - `backend/routes_chat.py`
  - `backend/scripts/rio3_smoke.py`
  - `backend/tests/unit/test_rio3_key_flow.py`
  - `docs/plano_pipeline/09_progresso_longo_prazo.md`
  - `docs/plano_pipeline/11_decisoes_otavio.md`
  - `docs/plano_pipeline/12_matriz_provider_fase.md`
  - `docs/plano_pipeline/13_plano_curto_paulo_rio3_render.md`
  - `frontend/index_v2.html`
  - `render.yaml`
- Ruido mantido fora do lote: `backend/.pytest_tmp`, scripts `frontend/take_*.py`,
  imagens em `frontend/tutorial-images-v2/cropped` e docs exploratorios 01-08.
- O harness Rio sem `RIO3_*` continua retornando `MISSING_RIO3_ENV`, o que
  confirma que a proxima virada de estado depende de provisionamento no Render,
  nao de correcoes adicionais no smoke local.

---

## Regras de Registro

- Nunca registrar segredo, token, URL de deploy hook, header de autorizacao ou
  preview de chave.
- Usar blocos pequenos e datados no Doc 09.
- Nao reescrever secoes grandes enquanto houver agentes paralelos.
- Distinguir fatos observados, estado informado e inferencias do Paulo.
- Se houver conflito entre local, GitHub e Render, registrar o conflito antes de
  agir.
