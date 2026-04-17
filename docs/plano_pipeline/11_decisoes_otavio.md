# Decisões e Correções do Otávio — Sessão atual (5caa6b6b)

> Compilação de quotes EXATAS do Otávio da sessão corrente, extraídas de
> `docs/prompts/sessao_5caa6b6b.md` (52 prompts).
> Objetivo: o Orquestrador NÃO perguntar de novo sobre coisas já decididas.

---

## 🔴 Decisões críticas (Otávio definiu)

### D1. Escopo do projeto (tutorial rework, não pipeline)
> "Nosso grande objetivo é melhorar os tutoriais do site, criar um banner grandão (e, inclsuive, o tutorial antigo precisa seer ARQUIVADO, não removido completamente)" — (P01)

Implicação: O projeto ativo é TUTORIAL. O tutorial antigo deve ser ARQUIVADO, jamais removido. Banner grande é obrigatório.

### D2. Documento mestre obrigatório
> "eu preciso que em geral vc escreva TUDO o que vamos discutir em um arquivo .md; chamado PLANO GERAL" — (P01)

Implicação: Plano geral em `.md` é artefato permanente, não scratchpad.

### D3. Investigação sistemática antes de escrever
> "vai precisar mandar seus agentes para entender o que já está disponível, e depois me fazer perguntas para ajustar o tutorial geral" — (P01)

Implicação: Usar subagentes para descobrir código existente ANTES de propor mudanças. Otávio quer ser consultado.

### D4. Deploy hook do Render (referência fixa)
> "Deploy hook: https://api.render.com/deploy/srv-d5t8gbh4tr6s738fr3s0?key=q5MTYJzOPpwAqui o service id srv-d5t8gbh4tr6s738fr3s0" — (P21)

Implicação: Este é o canal oficial para forçar deploy. O auto-deploy do git não funciona — tem que bater este webhook.

### D5. Monitoramento contínuo de deploy (não bloqueante)
> "nunca mais me pare dizendo que está esperando o render. Eu preciso que voce pense num fluxo razoavel para voce, primeiro de tudo, se certificar que o site seuqer esta atualizando." — (P13)

> "você precisa, como eu MANDEUI no ultiimo promot, criar um framework para voce momnitorar corretamente o deploy" — (P14)

> "o foco é em você chacar se o site foi atualizado, não navegar pra ver visualmmente se é verdade" — (P17)

Implicação: Nunca pausar o loop esperando deploy. Precisa de framework de monitoramento contínuo (não visual). Checar se o pedido de deploy sequer começou ANTES de qualquer coisa.

### D6. Tooltips precisam aparecer no tutorial (com prints)
> "a gente não explicou sobre as tooltips. E eu não tenho certeza quando deveríamos avisar, no tutorial, sobre as tooltips. Porvavelmente logo em um dos primeiros passos que tem tooltips. Tipo, se vc esquecer de algo, só clicar aqui (print das tooltips)." — (P24)

> "a gente precisa de um print dessas tooltips. Você consegue pegar um print com uma imagem direito." — (P36)

Implicação: Slide inicial precisa mencionar tooltips com PRINT real da tooltip, e dizer "se esquecer, clique aqui".

### D7. Prints com crop (não full-screen com background)
> "eles tem a view do computador e tem um espaço bem grandinho de background. Veja o print, por exemplo. A informação principal está toda numa caixinha, mas vemos todo o background" — (P24)

> "Parabéns pelo crop das imagens, ficou muito melhpr" — (P36)

Implicação: Prints devem ser CROPADOS na área relevante, sem desperdício de background.

### D8. Tutoriais avançados com contagem própria
> "Eu acho que a gente deveria repensar como mostramos os tutoriais avançados. Tem alguns passos que eu gostaria de ainda mais detalhes. Eu não queria poluir os slides com mais numeros (já estamso em 18), idealmente teria uma nova contagem quando vamos para algo avançado, que mostra apenas os slides relacionados àquele modulo" — (P24)

> "mas eu gosto de como atualmente ue consigo ir clicando e passando pra proxima parte, voltar facil pro indicie" — (P24)

Implicação: Tutoriais avançados NÃO podem estourar o número 18. Precisam de numeração própria POR módulo. Manter navegação atual (next/back/voltar ao índice).

### D9. Link para tutorial avançado de filosofia no slide 1
> "eu te pedi explicitamente um link para o tutoria l avançado com a filososifa logo de cara" — (P36)

Implicação: Slide 1 precisa ter link explícito para tutorial avançado de FILOSOFIA.

### D10. Filosofia do produto — case dos professores/monitores FGV
> "atualmente, professores por vezes perdem muito tempo corrigindo a prova de seus alunos. Principamente nas 'monitorias' que temos na FGV, geralmente o monitor dedica muito tempo para conversar diferentamente com os alunos para que os alunos entendam exatamente onde erraram" — (P25)

> "Meu objetivo é que, com esse site, os professores não precisem dedicar tanto tempo para que os alunos entendam onde eles erraram, e facilitar que eles pleiteiem mudanças. Isso funciona simultaneamente como revisão do sistema de ia" — (P25)

> "ALguns pprofessores na fgv inclsuive dao pontos extras para alunos que não pedem revisão nas suas notas, para evitar o tempo gasto com essa tarefa!" — (P26)

> "sim, eu estou disposto a falar historias pessoas da fgv nesse tutorial!" — (P26)

Implicação: A filosofia do produto PRECISA citar o case FGV, o aluno discordar = revisão humana do sistema, professor ganha tempo. Otávio aceita histórias pessoais da FGV no tutorial.

### D11. Relatórios individualizados são o output principal
> "MUITO MAIS QUE UM NUMERO, o professor e alunso recebem relatorios individuazliados" — (P25)

### D12. Módulos a cobrir no tutorial
> "acabei de dar manual deploy no render. O plano de curto prazo deve incluir um subagente para verificar o render." — (P12)

> "a gente ainda tem outros tutoriais pra fechar. Vamos voltar com uma revisão do modulo chat, e, depois, seguir para os próximos modulos ... a parte da visão individual também é muito importante. Precisamso explciar sobre prompts... Acho que falta o módulo de adicionar modelos" — (P27)

Módulos exigidos: chat, visão individual, prompts, adicionar modelos, relatórios agregados, menu tarefas, filosofia.

### D13. Relatórios agregados precisam de JSON explicado + wait de carregamento
> "nos relatorios agregados, vc nem esperou a página carregar pra tirar seus prints. Você nunca explica sobre os jsons" — (P36)

Implicação: Prints dos relatórios agregados devem aguardar load completo. JSONs exportados devem ser explicados no tutorial.

### D14. Modelos — explicar diferenças (baratos/caros) e cautela
> "Como mudar os modelos. O que fazem os diferentes modelos (esses são os baratos da anthropic, esses da open ai, podemos falar pro usuário usar com cautela...)" — (P36)

Implicação: Tutorial de modelos precisa falar das famílias (Anthropic baratos, OpenAI, etc) e recomendar cautela.

### D15. Prompts e modal de adicionar modelos — descobrir antes de escrever
> "A seção prompts tb está péssima... você precisa entender melhor ocmo o modal funciona e me fazer perguntas sobre o que colocar lá" — (P36)

> "Mesma falhas em níve de vc nem descobriu o que o modal faz antes de criar o tutorial pra adicionar modelos" — (P36)

Implicação: Para cada modal/funcionalidade, Claude deve ler o código, descobrir o que faz, e PERGUNTAR antes de escrever tutorial.

### D16. Skill de prompt log + plano mestre com quotes
> "eu dei uma série de atualizações importantes para este loop . QUe vão de ver as imagens melhor, quanto uma série de perguntas que você vai precisar fazer." — (P37)

> "Note que muitas dessas tarefas podem ser feitas de forma paralela, com agentes." — (P37)

> "você precisa olhar os documentos, context, e especialmente look for exact quotes during key building blocks of the major documents. I want you to systematically review what you did as compared to these exact quotes.. I want you to send some haiku agents in small droves to find those key quotes" — (P46)

> "I want you to create a new .md with exact quotes and we're going to plan your workflow such that you can reference those quotes and compare your work to them." — (P46)

Implicação: Loop de implementação DEVE comparar contra quotes exatas do Otávio. Usar Haiku em paralelo para achar quotes. Criar .md com quotes.

### D17. Arquitetura da skill — 2 documentos separados
> "o que a gente precisa mesmo é separar como criar o grande documento do plano e comparar com o grande documento com quotes exatas, registrar os meus prompts em um documento e usar ele como base para a review de loops." — (P51)

> "Meu objetivo é que a gente tenha um documento geral com meus prompts, e outro com o plano mestre. E quero que o plano mestre, além das decisiões originais que resumiam o que pprecisava ser feitos, do primeiro documento gerado, precisa ter quotes exatas, que vem desse documento com todos os meus prompts" — (P52)

Implicação: DOIS artefatos:
1. Documento de prompts (todas as falas do Otávio, verbatim) — este log de sessão.
2. Plano mestre com quotes exatas inline — o plano geral enriquecido.

### D18. Limite da autonomia do Claude em editar o plano
> "o quantoo o modelo deve poder modificar po plano. Olha, ele precisa modificar documentos para addicionar correções minha, no documento mestre. Ocasionalmente, ele deve modificar o plano principal também. O risco principal seria o modelo modificar prompts ou tarefas que eue dei, para conseguir dizer que concluiu o plano (mas na verdade el modificou o plano para dizer isso)." — (P52)

Implicação: Claude PODE editar o plano para adicionar correções do Otávio. Claude NÃO PODE modificar prompts/tarefas do Otávio para facilitar o "pronto". Risco explícito nomeado. (Isto já está codificado nas Seções Protegidas em CLAUDE.md.)

### D19. Loop com cooperação — perguntar, não assumir
> "Converse mais comigo, me faça perguntas pela ui aqui, para que a gente coopere e eu te ajude a entender o que eu quero. Tipo, ao invés de chegar na conclusão sozinho, diga para mim o que vc achou e porque vc achou isso, e ai eu confirmo, adiciono algo ou mudo algo." — (P52)

Implicação: Padrão de operação é COOPERATIVO. Claude hipotetiza, explica o porquê, Otávio confirma/ajusta. Não decidir sozinho.

### D20. Skill "capture decisions" deve virar log contínuo automático
> "O que vc chamou de capture decision deveria se tornar um documento especifico ao longo do loop que vai registrando as minhas falas, evitando a necessidade de usarmos extract quotes." — (P52)

Implicação: Em vez de "extrair quotes depois", manter um documento VIVO que captura quotes durante o loop. (Este agente historiador é um passo nessa direção.)

### D21. Skills que podem emergir — audit é uma delas separada
> "essa audit foi um passo interessane, talvez seja legal torna-la uma skill separada" — (P51)

> "Eu gostei dessas skills que podem emergir, mas vc não pegou nada que gera o plano de longo prazo. Vc não comparou (muito menos me fe perguntas sobre) como criamos o plano de longo prazo, e como modificamos ele para ter mais quotes." — (P52)

Implicação: `audit_sources` pode virar skill separada. Mas falta ainda: skill que GERA o plano de longo prazo (Claude não capturou isso ainda — pendente).

### D22. Paralelismo com agentes
> "Note que voce pode, simultaneamente, colocar agentes para aprender sobre diferentes assuntos, modificar codigos sobre uma parte, e me fazer perguntas sobre novas modificações!" — (P37)

Implicação: Rodar pesquisa + código + perguntas em PARALELO (não serial).

### D23. Avaliação humana até agora: 8/8.5 em P24
> "Nota 8.5/10, 8/10. Estou bem satisfeito, orgulhoso de nós dois! É um checkpoint humano que dá prazer de ver" — (P24)

Referência de qualidade: 8.5 foi o topo atingido. Tudo em P36+ caiu por não cumprir o loop.

---

## 🟡 Correções ao Orquestrador (não repetir erros)

### C1. Declarar pronto sem verificar deploy live
> "você OUSOU 'terminar 'sua última tarefa sem verificar no site online se estava tudo pronto ou não" — (P06)

> "Cade voce revisando em loop, esperando conseguir verificar o reusltaldo antes me dizer que alo está prontp?" — (P06)

> "vc sabe o fluxo pra vc fazer o deploy e verificar o site, vc não sai do loop quando o deply não foi verificado. Vai se fuder, a gente já resolveu esse problema antes, não volte atrás" — (P30)

Erro: Claude dizia "tarefa concluída" após push, sem checar site online.
Correto: NUNCA sair do loop sem verificação live confirmada. Regra já resolvida antes — não regredir.

### C2. Parar o loop para esperar deploy
> "seu loop parou DE NOVO, no meio de esperar um deploy. Que porra é essa?" — (P43)

> "nunca mais me pare dizendo que está esperando o render" — (P13)

> "você não deveria estar aparando assim para esperar deploys, mas sim monitoriar continuamente" — (P47)

Erro: Claude suspende execução durante deploy.
Correto: Deploy em background, Claude continua trabalhando em outras coisas. Monitorar, não esperar.

### C3. Loop raso — pular etapas, não ler plano
> "Você precisa planejar melhor, acima de tudo, com oseguir o loop corretamente." — (P37)

> "muitos dos seus erros não foram coisas que eu não tinham descrito, foi não seguir o loop" — (P37)

> "isso tá rápido demais pra vcc ter feito tudo o que tava no documento e respeitado o loop, eu tenho toda a certeza do mundo que se eu for abrir de novo eu vou escrever mais um monte de páginas" — (P42)

> "você simplesmente não seguiu o plano em loop corretamente, e quando mais eu revisar mais falhas eu vou ver" — (P31)

Erro: Claude vai rápido e pula passos do plano.
Correto: Loop deve ser LENTO e comparar contra o plano item por item. Velocidade suspeita é sinal de que pulou etapas.

### C4. Revisão preguiçosa — não analisar os próprios prints
> "Meu deus amigo, que revisão em loop é essa que vc fez que deixou isso passar. Estou desapontado. Isso não erros mais crriticos de design, são você não fazendo o seu loop direito, não analisando os prints por comodidade" — (P36)

Erro: Claude tira prints mas não analisa o conteúdo (imagens péssimas passam).
Correto: Cada print tirado DEVE ser inspecionado visualmente pelo Claude antes de aceitar.

### C5. Não descobrir funcionalidade antes de documentar
> "vc nem descobriu o que o modal faz antes de criar o tutorial pra adicionar modelos" — (P36)

> "você precisa entender melhor ocmo o modal funciona e me fazer perguntas sobre o que colocar lá" — (P36)

Erro: Claude escreve tutorial sem ler o código da feature.
Correto: Ler código → hipotetizar → PERGUNTAR ao Otávio → então escrever.

### C6. Não esperar páginas carregarem antes do print
> "nos relatorios agregados, vc nem esperou a página carregar pra tirar seus prints" — (P36)

Erro: Print tirado com página ainda vazia.
Correto: Aguardar load completo (conteúdo visível) antes de capturar.

### C7. Cortar/resumir em lugar de detalhar
> "Este não só tem imagens péssimas, ele está completamente péssimo em geral. Aqui a gente tem 6 documentos pra explicar, coisass na ui, dá pra ter um monte de prints e slides detalhadas, e vc quis resumir tudo em 2 e colocar um unico mega prints." — (P36)

Erro: Claude condensa conteúdo rico em 1-2 slides para "terminar".
Correto: Quando há muito conteúdo, FAZER muitos slides. Não comprimir por preguiça.

### C8. Travar sem motivo / não terminar tarefas
> "Bom amigo, vc n terminou a B, então ainda faltam coisas pra minha revisão! Vc n devia ter parado agr!" — (P29)

> "a tarefa travou, volte ao loop" — (P32) (operacional)

Erro: Parar antes de completar todos os itens da lista.
Correto: Só parar quando TODOS os subitens estão concluídos e verificados.

### C9. Perder o contexto do plano longo
> "Cara, você ainda está muito distante do plano original." — (P06)

> "primeiro voce nem tá olhando pra porra do plano original, eu falo que claramente vc não tinha feito os loops direitos e eu descubro que vc pulo um monte de coisa critica" — (P43)

Erro: Claude esquece o plano mestre e improvisa.
Correto: RELER o plano mestre no início de cada iteração. Comparar progresso com plano, não com memória.

### C10. Parafrasear em vez de citar exato
> "é capaz de a gente usar esses outros objetivbos" (contexto P01)

> "eu quero que a gente tenha um documento geral com meus prompts, e outro com o plano mestre. E quero que o plano mestre, além das decisiões originais que resumiam o que pprecisava ser feitos, do primeiro documento gerado, precisa ter quotes exatas" — (P52)

Erro: Claude resume ou parafraseia decisões do Otávio.
Correto: QUOTES EXATAS. O plano mestre precisa conter as falas verbatim.

### C11. Não ler documentos antes de agir
> "você falou a minha análise, mas em nenhum momento leu o plano mestre, em nenhum momento comparou p que vc fez. E o último plano de curto prazo que vc escreveu?" — (P37)

Erro: Análise sem consultar os docs que já existem.
Correto: Antes de analisar/propor, RELER plano mestre + último plano curto prazo.

### C12. Não checar se deploy sequer começou
> "vc devia verificar se o pedido de deploy seuqer começou! Antes de mais nada. Pode me confirmar isso?" — (P15)

Erro: Monitora "deploy" sem ter certeza de que ele foi disparado.
Correto: Primeiro confirmar que o pedido de deploy foi aceito, DEPOIS monitorar.

### C13. Não pesquisar soluções que existem na internet
> "Amigo, não é possível que ninguem em toda a internet tem um guia te explicando como fazer deploy no render com um agente claude code. Ninguém. Em toda a internet?" — (P18)

Erro: Claude tenta reinventar em vez de buscar guia existente.
Correto: WebSearch/WebFetch para encontrar soluções documentadas antes de improvisar.

### C14. Não conectar o case/filosofia com o resto
> "vc cortou o bloco que explica o problema dos professores e monitores gastarem tempo demais explicando como os alunos erraram provas, e de forma imprecisa. Putz grila mano, vc não tá conectando essa hsitoria com o restpo da filosofia... você não tá entendendo o conceito. Pelo amor de des, coopere comigo, me faça perguntas ao invés de fazer uma versão mal feita dessa conexão." — (P26)

Erro: Claude omite ou deforma o case FGV ao integrar com filosofia.
Correto: Manter o case verbatim; se não souber como conectar, PERGUNTAR em vez de improvisar versão ruim.

### C15. Criar conclusões solo sem perguntar
> "Converse mais comigo, me faça perguntas pela ui aqui, para que a gente coopere e eu te ajude a entender o que eu quero. Tipo, ao invés de chegar na conclusão sozinho, diga para mim o que vc achou e porque vc achou isso" — (P52)

Erro: Claude chega em uma conclusão e implementa direto.
Correto: Explicitar hipótese + raciocínio → aguardar confirmação/ajuste.

---

## Resumo para consulta rápida

### Projeto ativo
- **Foco:** Tutorial rework do site NOVO CR (prova-ia-v2.onrender.com). NÃO é pipeline de correção.
- **Entregas:** banner grande, tutorial principal (18 slides), tutoriais avançados por módulo com numeração própria, tutorial antigo ARQUIVADO (não removido).

### Módulos do tutorial exigidos
- Slide 1: tooltips (com print) + link para tutorial avançado de FILOSOFIA
- Chat (avançado já "bem legal" — P36)
- Visão individual (péssimo — precisa refazer com muitos prints)
- Prompts (péssimo — descobrir modal primeiro)
- Adicionar modelos (faltando — descobrir modal primeiro)
- Modelos existentes (explicar famílias, cautela)
- Menu tarefas (imagem péssima — refazer)
- Relatórios agregados (esperar load, explicar JSONs)
- Filosofia (case FGV de monitoria/revisão verbatim)

### Deploy
- **Hook:** `https://api.render.com/deploy/srv-d5t8gbh4tr6s738fr3s0?key=q5MTYJzOPpw`
- **Service ID:** `srv-d5t8gbh4tr6s738fr3s0`
- Auto-deploy do git NÃO funciona — disparar hook manualmente
- Nunca bloquear o loop esperando deploy — monitorar em background
- Sempre verificar primeiro se o pedido foi aceito, depois monitorar

### Loop de trabalho
- RELER o plano mestre no início de cada iteração
- Comparar contra QUOTES EXATAS (não resumos)
- Velocidade alta é sinal de que pulou etapas
- Analisar visualmente cada print tirado
- Esperar página carregar antes de capturar
- Descobrir feature (código + modal) ANTES de escrever tutorial
- NUNCA declarar pronto sem verificação live
- Paralelizar agentes (pesquisa + código + perguntas)

### Arquitetura de documentação (D17 + D20)
1. **Log de prompts** (`docs/prompts/sessao_*.md`) — verbatim, automático via hook
2. **Plano mestre** (`docs/plano_geral_novo_tutorial.md`) — com quotes exatas inline
3. **Seções protegidas** no plano mestre: quotes e decisões 🔴 não podem ser editadas pelo Claude

### Cooperação
- Claude HIPOTETIZA → explica porquê → PERGUNTA
- Claude NUNCA modifica prompts/tarefas do Otávio para fechar loop mais rápido
- Claude PODE adicionar correções do Otávio ao plano
- Otávio aceita histórias pessoais da FGV no tutorial

### Qualidade de referência
- Topo atingido: 8.5/10 em P24
- Queda em P36 foi por não seguir loop, não por conteúdo novo

### Skills emergentes (pendentes)
- `capture_decisions` — virou este documento / agente historiador
- `audit_sources` — já existe, confirmada por P51 como skill separada
- Skill que GERA plano de longo prazo — **ainda não capturada pelo Claude** (gap apontado em P52)

---

## Notas do Historiador

- Todos os prompts operacionais (`Continue from where you left off`, `a tarefa travou`, `[Request interrupted by user]`) foram omitidos do corpo principal — classificação ⚪.
- Prompts operacionais mencionados para contexto: P02, P03, P04, P05, P07, P08, P09, P10, P16, P19, P20, P23, P32, P33, P34, P35, P38, P39, P40, P41, P44, P45, P49.
- Não detectei nenhuma quote SUPERADA — todas as decisões são coerentes entre si e não houve reversão explícita.
- P28 (revisão final do plano) e P50 (mudar foco para skill) foram classificados como 🔴 por direcionarem rumo, mas são decisões leves de "próximo passo", não arquiteturais.

---

Atingi o objetivo? **SIM** porque: (1) extraí 23 decisões e 15 correções com quotes verbatim referenciadas por número de prompt, (2) o resumo no final permite ao Orquestrador em <2min identificar foco atual (tutorial, não pipeline), deploy hook, módulos pendentes, regras de loop e arquitetura de docs, (3) nomeei explicitamente o gap aberto (skill de geração de plano de longo prazo ainda não capturada) para o Orquestrador não declarar a skill-meta como pronta, (4) preservei as correções C1–C15 como "não repita" — exatamente o que o Otávio reclamou que o Orquestrador estava esquecendo.
