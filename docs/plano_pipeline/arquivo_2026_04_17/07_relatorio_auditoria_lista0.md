# Relatorio de Auditoria -- Atividade Lista0

**Data:** 2026-04-17
**Atividade ID:** `126e8b5ad7dd6d59`
**Turma:** 2026-1 (Algebra Linear Avancada)
**Materia ID:** `57861d16958965d2`

---

## Resumo

- **Total documentos:** 402
- **Bons:** 216 | **Fantasma:** 183 | **Incompletos:** 3 | **Invalidos:** 0

**Correcao posterior importante:** esta auditoria usou uma heuristica forte demais:
`conteudo=null` em `/api/documentos/{id}/conteudo` foi tratado como fantasma.
Depois ficou esclarecido que isso **nao vale para PDFs** de `prova_respondida`.
Entao os 64 `prova_respondida` abaixo **nao devem ser tratados como candidatos
automaticos a delecao** sem revisar `download/view` e storage.

### Por tipo de documento

| Tipo | BOM | FANTASMA | INCOMPLETO | Total |
|------|-----|----------|------------|-------|
| extracao_questoes | 29 | 0 | 0 | 29 |
| extracao_gabarito | 27 | 0 | 0 | 27 |
| extracao_respostas | 77 | 0 | 0 | 77 |
| prova_respondida | 0 | 64* | 0 | 64 |
| correcao | 28 | 43 | 3 | 74 |
| analise_habilidades | 19 | 24 | 0 | 43 |
| relatorio_final | 36 | 50 | 0 | 86 |
| gabarito | 0 | 1 | 0 | 1 |
| enunciado | 0 | 1 | 0 | 1 |

**Observacao critica:** TODOS os 64 docs `prova_respondida` tem `conteudo=null`
em `/conteudo`, mas isso hoje e entendido como **limite do endpoint para PDFs**,
nao como prova suficiente de fantasma. Trate essa classificacao como historica e
desatualizada.

---

## Documentos Base (nivel atividade)

| Tipo | Qtd | Status | Detalhes |
|------|-----|--------|----------|
| extracao_questoes | 29 | BOM (todas) | Duplicatas: 29 copias identicas (uma por execucao de pipeline). Todas validas com 7 questoes. |
| extracao_gabarito | 27 | BOM (todas) | Duplicatas: 27 copias. Todas com chave `respostas`. |
| gabarito | 1 | FANTASMA | `dbfe3a77a631489f` -- conteudo=null |
| enunciado | 1 | FANTASMA | `5dc75513e958c25b` -- conteudo=null |

**Problema:** Os docs `gabarito` e `enunciado` sao registros placeholder sem conteudo. As 29 copias de extracao_questoes e 27 de extracao_gabarito sao redundancia pura do pipeline re-executando a extracao base a cada aluno.

---

## Por Aluno

### Alunos com prova e correcao (28 com correcao BOM)

| # | Aluno | ID | Docs BOM | Docs Fantasma | Nota |
|---|-------|----|----------|---------------|------|
| 1 | ALVARO JOEL TICONA MOTTA | 40ab839a5340e39a | 13 | 12 | tem correcao |
| 2 | ANA VICTORIA MACHADO VILELA ROCHA | f625e788402b9d8b | 4 | 4 | tem correcao |
| 3 | Ana Beatriz Botacim Rodrigues | 244423c43d59df0e | 6 | 5 | tem correcao |
| 4 | Ana Julia da Silva | 015ffc573fca927f | 5 | 5 | tem correcao |
| 5 | BEATRIZ PIMENTA NORA | 86765eb16a28997c | 4 | 2 | tem correcao |
| 6 | Cleidyene Renata Silva Ribeiro | 9dbb6e509fb85d7c | 4 | 2 | tem correcao |
| 7 | EDILTON BRANDAO DE SOUSA | 5e178a4a9bcd1ac6 | 4 | 7 | tem correcao |
| 8 | Elainne Alejandra Gutierrez Rohs | 9ab2d50651700d9e | 4 | 4 | tem correcao |
| 9 | Gabriel Alianca de Jesus Crisostomo | 706022cc019b9e64 | 5 | 5 | tem correcao |
| 10 | Gabriel Schuenker Rosa de Oliveira | 382e5ec2d4c27183 | 5 | 7 | tem correcao |
| 11 | GUSTAVO DE OLIVEIRA DA SILVA | 7eb7b151466d5893 | 5 | 7 | tem correcao |
| 12 | Jaime Willian Carneiro da Silva | 45b01c2616272c0d | 3 | 9 | tem correcao |
| 13 | Joel Gil Medeiros de Oliveira | eca46b98c3eea088 | 3 | 4 | tem correcao |
| 14 | Jordana Martinelli | 457b04cfe16fb06b | 4 | 7 | tem correcao |
| 15 | Jose Pedro Dresch | f0d05154c36d4cd4 | 5 | 3 | tem correcao (sem relatorio_final BOM) |
| 16 | Joao Gabriel Carneiro Calbo | f4949052af58ce93 | 5 | 4 | tem correcao |
| 17 | LEVI JOEL CASTILLON URQUIZA | fa425037b1946029 | 4 | 9 | tem correcao |
| 18 | Leonardo Verissimo | 361ec05035afffba | 6 | 7 | tem correcao |
| 19 | Leonidas Caetano da Silva | e4064c7457a6a6b4 | 3 | 6 | tem correcao |
| 20 | Luis Eduardo Weigert Weiss | 85d668e2c18b49c3 | 3 | 5 | tem correcao |
| 21 | Maria Leticia dos Santos Morais | 4a70f82711d0f65a | 2 | 3 | tem correcao |
| 22 | Murilo Granemann de Souza | 742e1242a49b3059 | 2 | 3 | tem correcao |
| 23 | Nina Leao Fonseca | bfec7953cffdc410 | 5 | 9 | tem correcao |
| 24 | Osmar Caio da Costa Silva | 133edd15ff34b4bf | 5 | 5 | tem correcao |
| 25 | Paulo Vitor do Amaral Gomes | c280b4312465b757 | 4 | 4 | tem correcao |
| 26 | Pedro Santos Tokar | 010582072224e2ff | 4 | 7 | tem correcao |
| 27 | PHELIPE GABRIEL LIMA DA SILVA | bac3eb8ff0ee23b2 | 4 | 4 | tem correcao |
| 28 | Policarpo de Sousa Torres Junior | 110f4089aa33c5a2 | 3 | 8 | tem correcao |

### Alunos com prova sem correcao (10) -- CANDIDATOS A TESTE

| # | Aluno | ID | Etapas completadas | Etapas faltando | Motivo da falha |
|---|-------|----|--------------------|-----------------|-----------------|
| 1 | Eric Manoel Ribeiro de Sousa | 660e9421b246ad3f | extrair_questoes, extrair_gabarito, extrair_respostas | **corrigir** (pode executar), analisar_habilidades | Pipeline parou antes da correcao. Tem extracao_respostas BOM. |
| 2 | Henrique Coelho Beltrao | fb881a3961022dd9 | extrair_questoes, extrair_gabarito, extrair_respostas | **corrigir** (pode executar), analisar_habilidades | Pipeline parou antes da correcao. Tem extracao_respostas BOM. |
| 3 | Jean Gabriel Domingueti | 82cd26360e254a92 | extrair_questoes, extrair_gabarito, extrair_respostas | **corrigir** (pode executar), analisar_habilidades | Pipeline parou antes da correcao. Tem extracao_respostas BOM. |
| 4 | Luiz Eduardo Bravin | 8307341d7c135a46 | extrair_questoes, extrair_gabarito, extrair_respostas | **corrigir** (pode executar), analisar_habilidades | Pipeline parou antes da correcao. Tem extracao_respostas BOM. |
| 5 | Pablo Levy Fernandes Alcantara | f2828766a2a91e9a | extrair_questoes, extrair_gabarito, extrair_respostas | **corrigir** (pode executar), analisar_habilidades | Pipeline parou antes da correcao. Tem extracao_respostas BOM. |
| 6 | Pedro Marrochio Lacerda de Abreu | f93a9eb29e6654a2 | extrair_questoes, extrair_gabarito, extrair_respostas | **corrigir** (pode executar), analisar_habilidades | Pipeline parou antes da correcao. Tem extracao_respostas BOM. |
| 7 | RAFAEL CARVALHO NEVES | 22f48fd93550d547 | extrair_questoes, extrair_gabarito, extrair_respostas | **corrigir** (pode executar), analisar_habilidades | Pipeline parou antes da correcao. Tem extracao_respostas BOM. |
| 8 | LUISA VILLANUEVA GUERRERO | dfaa27d39b2dd166 | extrair_questoes, extrair_gabarito | **extrair_respostas** (pode executar), corrigir, analisar_habilidades | Nao tem extracao_respostas. Parou mais cedo. |
| 9 | Luiz Antonio Alves de Lima | c4b45ee6b64d394f | extrair_questoes, extrair_gabarito | **extrair_respostas** (pode executar), corrigir, analisar_habilidades | Nao tem extracao_respostas. Parou mais cedo. |
| 10 | Matheus Vilarino de Souza Pinto | 9219cc0d07ba600a | extrair_questoes, extrair_gabarito | **extrair_respostas** (pode executar), corrigir, analisar_habilidades | Nao tem extracao_respostas. Parou mais cedo. |

**Nota:** Os 7 primeiros (1-7) tem extracao_respostas OK e estao prontos para correcao imediata (`pode_executar: true`).
Os 3 ultimos (8-10) precisam primeiro da extracao de respostas.

Curiosamente, a API marca `gerar_relatorio` como "concluida" para os alunos 1-7, mas os relatorios gerados sao fantasma (conteudo=null ou `{{nota_final}}`). O pipeline gerou o registro sem conteudo real.

### Alunos fantasma (3) -- correcao sem prova_respondida

| # | Aluno | ID | Docs encontrados | Conteudo real ou erro? |
|---|-------|----|------------------|-----------------------|
| 1 | ALICE BARROS LOURENCINI PALAORO | 9b0f104fa9e7c5d9 | extracao_respostas (1 BOM), correcao (2: 1 BOM, 1 null), analise_habilidades (2: ambos null), relatorio_final (1 null) | Misto: tem extracao_respostas e 1 correcao validos, mas sem prova. Pipeline executou com dados de outra fonte? |
| 2 | FABRICIO DALVI VENTURIM | cdec224bb0733be0 | extracao_respostas (1 BOM), correcao (2: 1 BOM, 1 null) | Tem extracao e 1 correcao validos mas sem prova_respondida. |
| 3 | RAPHAEL FELBERG LEVY | 85b4e1c73e9a37f0 | extracao_respostas (1 BOM), correcao (2: 1 BOM, 1 null) | Mesmo padrao: extracao e correcao validos sem prova. |

**Diagnostico:** Estes 3 alunos tiveram o pipeline executado (possivelmente manualmente ou por bug), gerando extracao_respostas e correcao a partir de dados que nao vieram via upload de prova. Cada um tem uma correcao nula (tentativa falha) e uma correcao com conteudo real.

### Alunos sem prova (2 adicionais -- so extracao_respostas)

| Aluno | ID | Docs | Situacao |
|-------|----|------|----------|
| Antonio Francisco Batista Filho | e78ba1120686ef07 | extracao_respostas (1 BOM) | Pipeline parcial: extraiu respostas sem prova. |
| Rodrigo Gomes Hutz Pintucci | 34ac263b0140057f | extracao_respostas (1 BOM) | Pipeline parcial: extraiu respostas sem prova. |

### Alunos sem nenhum documento (estimativa)

A turma tem ~66 alunos (baseado nos dados do sistema). 43 alunos tem pelo menos 1 doc. ~23 alunos nao tem nenhum documento.

---

## Documentos Marcados para Revisao / Possivel Delecao

### Prioridade 1: Revisar os marcados como fantasma antes de deletar

Nao usar esta secao como ordem automatica de delecao. Depois da nota tecnica sobre
`/conteudo` em PDFs, a lista precisa ser reclassificada antes de qualquer limpeza.

#### Por tipo:

| Tipo | Qtd a deletar | Motivo |
|------|---------------|--------|
| prova_respondida | 0 por ora | REVISAR: PDF pode aparecer como `conteudo=null` em `/conteudo` e continuar valido em `download/view`. |
| relatorio_final | 50 | Null ou template `{{nota_final}}` nao preenchido. |
| correcao | 43 | Null -- tentativas de correcao que falharam. |
| analise_habilidades | 24 | Null -- tentativas que falharam. |
| gabarito | 1 | Placeholder null. |
| enunciado | 1 | Placeholder null. |

#### Detalhamento -- lista historica que precisa reclassificacao:

| Doc ID | Tipo | Aluno | Motivo | Classificacao |
|--------|------|-------|--------|---------------|
| dbfe3a77a631489f | gabarito | (base) | conteudo=null | FANTASMA |
| 5dc75513e958c25b | enunciado | (base) | conteudo=null | FANTASMA |
| 5dc489a4c857689a | relatorio_final | ALVARO JOEL | conteudo=null | FANTASMA |
| 5243d18635b3e89d | relatorio_final | ALVARO JOEL | conteudo=null | FANTASMA |
| 19397d98f1e2316b | analise_habilidades | ALVARO JOEL | conteudo=null | FANTASMA |
| 9a104922ff9be63a | analise_habilidades | ALVARO JOEL | conteudo=null | FANTASMA |
| f8317a1cf3b4c966 | analise_habilidades | ALVARO JOEL | conteudo=null | FANTASMA |
| 8c661db7863fc8ab | correcao | ALVARO JOEL | conteudo=null | FANTASMA |
| 5d82aa5350273d01 | correcao | ALVARO JOEL | conteudo=null | FANTASMA |
| 8159809257fc1c7f | relatorio_final | ALICE BARROS | conteudo=null | FANTASMA |
| ec1303b17797472d | analise_habilidades | ALICE BARROS | conteudo=null | FANTASMA |
| b17c1f8cb2070f51 | correcao | ALICE BARROS | conteudo=null | FANTASMA |
| d06d386a2ee8d563 | correcao | RAPHAEL FELBERG | conteudo=null | FANTASMA |
| 24872ad4ac3459d4 | correcao | FABRICIO DALVI | conteudo=null | FANTASMA |
| a793d686d2f93600 | relatorio_final | RAFAEL CARVALHO | conteudo=null | FANTASMA |
| 380fc48635cf4149 | relatorio_final | RAFAEL CARVALHO | template {{nota_final}} | FANTASMA |
| 97eb28e5295802a3 | correcao | Policarpo | conteudo=null | FANTASMA |
| 1bb8d4225eda5c6c | correcao | Policarpo | conteudo=null | FANTASMA |
| e5214e38138bc1b7 | relatorio_final | Policarpo | conteudo=null | FANTASMA |
| 0e6e1e5989ee52d4 | relatorio_final | Policarpo | template {{nota_final}} | FANTASMA |
| 717a76f4e7d97368 | analise_habilidades | PHELIPE GABRIEL | conteudo=null | FANTASMA |
| 5e82f147aef46046 | analise_habilidades | PHELIPE GABRIEL | conteudo=null | FANTASMA |
| d3eac31638449834 | relatorio_final | Pedro Santos Tokar | conteudo=null | FANTASMA |
| 6dbff6bbbadd3bb2 | relatorio_final | Pedro Santos Tokar | conteudo=null | FANTASMA |
| fd3bce6daa35ce0d | correcao | Pedro Santos Tokar | conteudo=null | FANTASMA |
| 2b153c920ee47e04 | relatorio_final | Pedro Marrochio | conteudo=null | FANTASMA |
| b74e35ff3bbcee1b | relatorio_final | Pedro Marrochio | template {{nota_final}} | FANTASMA |
| b2622191d95dfec4 | relatorio_final | Pedro Marrochio | conteudo=null | FANTASMA |
| 4f94a40a49bb7ba8 | relatorio_final | Paulo Vitor | conteudo=null | FANTASMA |
| 58fdb08b975a6643 | relatorio_final | Paulo Vitor | conteudo=null | FANTASMA |
| 269ae1eea17fd2f0 | relatorio_final | Pablo Levy | conteudo=null | FANTASMA |
| 119be828c669d010 | relatorio_final | Osmar Caio | conteudo=null | FANTASMA |
| 72cc233d9b921130 | analise_habilidades | Osmar Caio | conteudo=null | FANTASMA |
| 249febf37fef4d0c | correcao | Osmar Caio | conteudo=null | FANTASMA |
| 5298a5f9a0859fb2 | relatorio_final | Nina Leao | conteudo=null | FANTASMA |
| 9f1ad48877f4cb2b | analise_habilidades | Nina Leao | conteudo=null | FANTASMA |
| 01514b47beb2a503 | analise_habilidades | Nina Leao | conteudo=null | FANTASMA |
| 64dd551ce453d000 | analise_habilidades | Nina Leao | conteudo=null | FANTASMA |
| 80dbd1d8abd46463 | correcao | Nina Leao | conteudo=null | FANTASMA |
| e9a00cd8a00410b4 | correcao | Nina Leao | conteudo=null | FANTASMA |
| f48f0621453782a9 | relatorio_final | Murilo Granemann | conteudo=null | FANTASMA |
| 57fcf5fbdd626528 | relatorio_final | Murilo Granemann | conteudo=null | FANTASMA |
| 8195c8f06cba7aa7 | relatorio_final | Maria Leticia | conteudo=null | FANTASMA |
| 3237b5355ae256c1 | correcao | Maria Leticia | conteudo=null | FANTASMA |
| 57e0b12bcf9865a6 | relatorio_final | Luiz Eduardo Bravin | conteudo=null | FANTASMA |
| 58a934133acbd658 | relatorio_final | Luis Eduardo Weigert | conteudo=null | FANTASMA |
| f9262d79336646ee | correcao | Luis Eduardo Weigert | conteudo=null | FANTASMA |
| 93c73c1c58a0c2d3 | correcao | Luis Eduardo Weigert | conteudo=null | FANTASMA |
| 2c9d01f5b7edf2b4 | correcao | Luis Eduardo Weigert | conteudo=null | FANTASMA |
| c7859819acf0eeda | relatorio_final | LEVI JOEL | conteudo=null | FANTASMA |
| 74ec72813d04dc8c | relatorio_final | LEVI JOEL | conteudo=null | FANTASMA |
| 382c5a89f1950c29 | analise_habilidades | LEVI JOEL | conteudo=null | FANTASMA |
| 0cbbac0bda8e3870 | analise_habilidades | LEVI JOEL | conteudo=null | FANTASMA |
| 50cd3a6cfa44f5cc | analise_habilidades | LEVI JOEL | conteudo=null | FANTASMA |
| b0483512fcd77f5b | correcao | LEVI JOEL | conteudo=null | FANTASMA |
| 2b957a6cbd4d3268 | correcao | LEVI JOEL | conteudo=null | FANTASMA |
| e4268246a5a3b314 | relatorio_final | Leonidas Caetano | conteudo=null | FANTASMA |
| 22536b1fd75b6d27 | correcao | Leonidas Caetano | conteudo=null | FANTASMA |
| c8c7516bb01d7bff | correcao | Leonidas Caetano | conteudo=null | FANTASMA |
| a411d43e9e6c4809 | correcao | Leonidas Caetano | conteudo=null | FANTASMA |
| 6a7242ed54adb204 | relatorio_final | Leonardo Verissimo | conteudo=null | FANTASMA |
| b037f93078243577 | relatorio_final | Leonardo Verissimo | conteudo=null | FANTASMA |
| b11131795c33a8b9 | analise_habilidades | Leonardo Verissimo | conteudo=null | FANTASMA |
| 3ea9085693aa68d7 | correcao | Leonardo Verissimo | conteudo=null | FANTASMA |
| 1deb98b815c48374 | analise_habilidades | Jose Pedro Dresch | conteudo=null | FANTASMA |
| 24a30e1ad3603876 | analise_habilidades | Jose Pedro Dresch | conteudo=null | FANTASMA |
| 6626224b6c35040c | relatorio_final | Jordana Martinelli | conteudo=null | FANTASMA |
| cb7c489b93b0ed08 | relatorio_final | Jordana Martinelli | conteudo=null | FANTASMA |
| 8752df1f11f4ce91 | relatorio_final | Jordana Martinelli | conteudo=null | FANTASMA |
| 627694df9efec759 | correcao | Jordana Martinelli | conteudo=null | FANTASMA |
| 28cd86ada6e11838 | correcao | Jordana Martinelli | conteudo=null | FANTASMA |
| 9e327409486d733f | correcao | Joel Gil | conteudo=null | FANTASMA |
| 11ea272f73d8df37 | relatorio_final | Joel Gil | conteudo=null | FANTASMA |
| f6cb448f5cca630a | relatorio_final | Joel Gil | conteudo=null | FANTASMA |
| 95245c994d0ae5ff | relatorio_final | Joao Gabriel | conteudo=null | FANTASMA |
| 17df51dd6a77486c | analise_habilidades | Joao Gabriel | conteudo=null | FANTASMA |
| e7ae1035d7c835f8 | analise_habilidades | Joao Gabriel | conteudo=null | FANTASMA |
| 5c76e5742f8e4e36 | correcao | Joao Gabriel | conteudo=null | FANTASMA |
| 1eb0c147b884299a | relatorio_final | Jean Gabriel | conteudo=null | FANTASMA |
| b1b2415c925b0b6e | analise_habilidades | Jaime Willian | conteudo=null | FANTASMA |
| bd0091a5e14d5b1b | correcao | Jaime Willian | conteudo=null | FANTASMA |
| 20ba743ae7847da6 | correcao | Jaime Willian | conteudo=null | FANTASMA |
| f1754b1e5f5c535f | correcao | Jaime Willian | conteudo=null | FANTASMA |
| 0a701d419dfac5f1 | correcao | Jaime Willian | conteudo=null | FANTASMA |
| c1c4e69badda6901 | correcao | Jaime Willian | conteudo=null | FANTASMA |
| f7c97387c86b38a1 | relatorio_final | Henrique Coelho | conteudo=null | FANTASMA |
| 761a63b0449f4346 | relatorio_final | GUSTAVO | conteudo=null | FANTASMA |
| e31dfacc62b34b36 | relatorio_final | GUSTAVO | conteudo=null | FANTASMA |
| 27530e5081dd3502 | analise_habilidades | GUSTAVO | conteudo=null | FANTASMA |
| d58b2e0bc1d4d69b | analise_habilidades | GUSTAVO | conteudo=null | FANTASMA |
| 280862f3ae015948 | correcao | GUSTAVO | conteudo=null | FANTASMA |
| 111d62e9737fa0f0 | correcao | GUSTAVO | conteudo=null | FANTASMA |
| 71f795f72e87bb39 | relatorio_final | Gabriel Schuenker | conteudo=null | FANTASMA |
| ed5c107cc60d037b | analise_habilidades | Gabriel Schuenker | conteudo=null | FANTASMA |
| c0b2710775148834 | relatorio_final | Gabriel Schuenker | conteudo=null | FANTASMA |
| a48a97a20f477205 | relatorio_final | Gabriel Schuenker | template {{nota_final}} | FANTASMA |
| 5730db2ae83acddf | correcao | Gabriel Schuenker | conteudo=null | FANTASMA |
| 020e5d3502813787 | relatorio_final | Gabriel Alianca | conteudo=null | FANTASMA |
| ced1f5c69e11cd68 | analise_habilidades | Gabriel Alianca | conteudo=null | FANTASMA |
| 80f1768bf52f1399 | correcao | Gabriel Alianca | conteudo=null | FANTASMA |
| 514cc6044f1d70bc | relatorio_final | Eric Manoel | conteudo=null | FANTASMA |
| 4e5b96da14aa2144 | relatorio_final | Elainne Alejandra | conteudo=null | FANTASMA |
| 17ed8151acaa0340 | analise_habilidades | Elainne Alejandra | conteudo=null | FANTASMA |
| 9333a54f695104b1 | correcao | Elainne Alejandra | conteudo=null | FANTASMA |
| c88dc81d7c7c33f8 | relatorio_final | EDILTON BRANDAO | conteudo=null | FANTASMA |
| 402ada5e464189de | relatorio_final | EDILTON BRANDAO | conteudo=null | FANTASMA |
| d4c1f5af8334c697 | correcao | EDILTON BRANDAO | conteudo=null | FANTASMA |
| 043e65bbd101e6cc | correcao | EDILTON BRANDAO | conteudo=null | FANTASMA |
| cd4dd51f316c6a19 | relatorio_final | Cleidyene Renata | conteudo=null | FANTASMA |
| 5c92221e1f6075f9 | relatorio_final | ANA VICTORIA | conteudo=null | FANTASMA |
| c2efaade335a9083 | correcao | ANA VICTORIA | conteudo=null | FANTASMA |
| f7423646a471f81c | correcao | ANA VICTORIA | conteudo=null | FANTASMA |
| 8c8baa6c7cec7d81 | relatorio_final | Ana Julia | conteudo=null | FANTASMA |
| 1ffddcf25e045a84 | relatorio_final | Ana Julia | conteudo=null | FANTASMA |
| cb20a8179b27f8f7 | correcao | Ana Julia | conteudo=null | FANTASMA |
| 09b1938cf9105182 | correcao | Ana Julia | conteudo=null | FANTASMA |
| a3a39e20c05229e3 | correcao | Ana Beatriz | conteudo=null | FANTASMA |
| c011d41996610616 | correcao | Ana Beatriz | conteudo=null | FANTASMA |
| d013bbb42ca1c610 | relatorio_final | Ana Beatriz | conteudo=null | FANTASMA |
| 0d9fbe15e3188a82 | prova_respondida | EDILTON BRANDAO | conteudo=null | FANTASMA |
| 0bc54883e35fa988 | prova_respondida | EDILTON BRANDAO | conteudo=null | FANTASMA |
| 18f4b9c96c825306 | prova_respondida | EDILTON BRANDAO | conteudo=null | FANTASMA |
| 4d12adc56d8df502 | prova_respondida | Paulo Vitor | conteudo=null | FANTASMA |
| e188f490c80173c9 | prova_respondida | Policarpo | conteudo=null | FANTASMA |
| ac7bd8a56d29710f | prova_respondida | Policarpo | conteudo=null | FANTASMA |
| c3a522014dd4740e | prova_respondida | Policarpo | conteudo=null | FANTASMA |
| 2d46a09f184293ad | prova_respondida | Policarpo | conteudo=null | FANTASMA |
| 940e9a6bcb50773e | prova_respondida | GUSTAVO | conteudo=null | FANTASMA |
| cde4af157c488e5d | prova_respondida | RAFAEL CARVALHO | conteudo=null | FANTASMA |
| d8e380ee512a1cb2 | prova_respondida | LUISA VILLANUEVA | conteudo=null | FANTASMA |
| 574e4c153ebcbfa0 | prova_respondida | LEVI JOEL | conteudo=null | FANTASMA |
| f7cbf86750d8cce1 | prova_respondida | BEATRIZ PIMENTA | conteudo=null | FANTASMA |
| 8f41ca9848a53e3b | prova_respondida | ANA VICTORIA | conteudo=null | FANTASMA |
| 95aba9192219b65d | prova_respondida | ALVARO JOEL | conteudo=null | FANTASMA |
| cf7d8a11b9e8b0db | prova_respondida | Joel Gil | conteudo=null | FANTASMA |
| 3a8bafd366e7a0d8 | prova_respondida | Leonidas Caetano | conteudo=null | FANTASMA |
| fbed841926ce13bf | prova_respondida | Leonidas Caetano | conteudo=null | FANTASMA |
| 11da85dd0881f18f | prova_respondida | Maria Leticia | conteudo=null | FANTASMA |
| 7d1cf8b551a3910b | prova_respondida | Pedro Marrochio | conteudo=null | FANTASMA |
| 365b99c9fdd14907 | prova_respondida | Pedro Marrochio | conteudo=null | FANTASMA |
| 46833720d5f0d330 | prova_respondida | Pablo Levy | conteudo=null | FANTASMA |
| 624f1f8839adf87a | prova_respondida | Pablo Levy | conteudo=null | FANTASMA |
| 00b994df7cc5f646 | prova_respondida | Luiz Antonio | conteudo=null | FANTASMA |
| d504425ae3da6be7 | prova_respondida | Luiz Antonio | conteudo=null | FANTASMA |
| a86520696d7bd080 | prova_respondida | Osmar Caio | conteudo=null | FANTASMA |
| 45a05ae7d02d3ca2 | prova_respondida | Ana Julia | conteudo=null | FANTASMA |
| 27da373d284d5690 | prova_respondida | Ana Julia | conteudo=null | FANTASMA |
| 94bbafdfa13a63c7 | prova_respondida | Cleidyene Renata | conteudo=null | FANTASMA |
| 5b021d490a3d9c64 | prova_respondida | Joao Gabriel | conteudo=null | FANTASMA |
| 84bad4da95bccad2 | prova_respondida | Murilo Granemann | conteudo=null | FANTASMA |
| 39ffed65f534cb1e | prova_respondida | Luis Eduardo Weigert | conteudo=null | FANTASMA |
| 5f01929adbfe7ef7 | prova_respondida | Jordana Martinelli | conteudo=null | FANTASMA |
| bdd19dc80131d3b9 | prova_respondida | Ana Beatriz | conteudo=null | FANTASMA |
| ffed600778f3d423 | prova_respondida | Elainne Alejandra | conteudo=null | FANTASMA |
| ac094a9558b9cb1d | prova_respondida | PHELIPE GABRIEL | conteudo=null | FANTASMA |
| 2f9b2d90ab7ae6e6 | prova_respondida | Jose Pedro Dresch | conteudo=null | FANTASMA |
| 6e9c0e5175058067 | prova_respondida | Nina Leao | conteudo=null | FANTASMA |
| 470c5024567e5b7c | prova_respondida | Nina Leao | conteudo=null | FANTASMA |
| 696aefac103e6078 | prova_respondida | Gabriel Schuenker | conteudo=null | FANTASMA |
| f024adeb469c8135 | prova_respondida | Jaime Willian | conteudo=null | FANTASMA |
| 44a3cac5b6cd2614 | prova_respondida | Jaime Willian | conteudo=null | FANTASMA |
| e5324a5f2d2e3bf2 | prova_respondida | Henrique Coelho | conteudo=null | FANTASMA |
| 21d5b85b27669f03 | prova_respondida | Matheus Vilarino | conteudo=null | FANTASMA |
| 9a1661fd498de92a | prova_respondida | Matheus Vilarino | conteudo=null | FANTASMA |
| 66e80bb003e369a1 | prova_respondida | Luiz Eduardo Bravin | conteudo=null | FANTASMA |
| b36a1cb72c2e1d7a | prova_respondida | Jean Gabriel | conteudo=null | FANTASMA |
| 6f59ab156738252c | prova_respondida | Leonardo Verissimo | conteudo=null | FANTASMA |
| f60d37284d616ca4 | prova_respondida | Eric Manoel | conteudo=null | FANTASMA |
| 01a866c7a5794a55 | prova_respondida | Pedro Santos Tokar | conteudo=null | FANTASMA |
| 2eeb35d7afd0daa7 | prova_respondida | Gabriel Alianca | conteudo=null | FANTASMA |
| c81e727e326cc358 | prova_respondida | Gabriel Alianca | conteudo=null | FANTASMA |
| 2db68f7cec2b944f | prova_respondida | Luiz Eduardo Bravin | conteudo=null | FANTASMA |
| 495bbdfc89d03f46 | prova_respondida | Jean Gabriel | conteudo=null | FANTASMA |
| b268627be3c0e452 | prova_respondida | Leonardo Verissimo | conteudo=null | FANTASMA |
| bac04fcf3a92c7e3 | prova_respondida | Eric Manoel | conteudo=null | FANTASMA |
| eedaca31eac7319d | prova_respondida | Pedro Santos Tokar | conteudo=null | FANTASMA |
| b63e23aaa9ca89cf | prova_respondida | Gabriel Alianca | conteudo=null | FANTASMA |
| 544b4b6be4addc7f | prova_respondida | Gabriel Alianca | conteudo=null | FANTASMA |
| 9221011e19c67fe3 | prova_respondida | Gabriel Schuenker | conteudo=null | FANTASMA |
| 7cca65eda4c27be0 | prova_respondida | Jaime Willian | conteudo=null | FANTASMA |
| bdb7414867b41381 | prova_respondida | Matheus Vilarino | conteudo=null | FANTASMA |
| 3ba9f19b3bde540a | prova_respondida | Leonardo Verissimo | conteudo=null | FANTASMA |
| 8e47db58ad05a55d | prova_respondida | Pedro Santos Tokar | conteudo=null | FANTASMA |

### Prioridade 2: Incompletos (3 docs)

| Doc ID | Tipo | Aluno | Motivo | Classificacao |
|--------|------|-------|--------|---------------|
| b8264a663166742c | correcao | Policarpo de Sousa Torres Junior | JSON valido sem campo `nota_final` | INCOMPLETO |
| 50f07203937236ed | correcao | Pedro Santos Tokar | JSON valido sem campo `nota_final` | INCOMPLETO |
| 4a57af1d01303876 | correcao | Paulo Vitor do Amaral Gomes | JSON valido sem campo `nota_final` | INCOMPLETO |

### Prioridade 3: Duplicatas de base (recomendacao)

As 29 copias de `extracao_questoes` e 27 copias de `extracao_gabarito` sao todas BOM mas totalmente redundantes. Manter apenas 1 de cada e deletar as demais economizaria ~54 registros.

---

## Aluno Selecionado para Teste

**Eric Manoel Ribeiro de Sousa** (`660e9421b246ad3f`)

### Justificativa:

1. **Pipeline pronto para correcao:** A etapa `corrigir` esta marcada como `pode_executar: true`. Todas as pre-condicoes estao satisfeitas (extracao_questoes, extracao_gabarito, extracao_respostas OK).

2. **Minimo de lixo:** Tem apenas 2 docs fantasma (relatorio_final null) alem das provas null. Outros candidatos como Pedro Marrochio tem 4 relatorio_final fantasma e Jean Gabriel tem docs duplicados.

3. **Nome simples:** Sem caracteres especiais que possam causar problemas.

4. **Representativo:** Falhou no mesmo ponto que os outros 6 candidatos "prontos" (1-7), entao serve como caso de teste generalizado.

### Para executar o teste:

```bash
# Verificar status atual
curl -s "https://ia-educacao-v2.onrender.com/api/processamento/status/126e8b5ad7dd6d59?aluno_id=660e9421b246ad3f"

# Executar correcao (proxima etapa)
curl -X POST "https://ia-educacao-v2.onrender.com/api/processamento/executar/126e8b5ad7dd6d59" \
  -H "Content-Type: application/json" \
  -d '{"aluno_id": "660e9421b246ad3f", "etapa": "corrigir"}'
```

---

## Diagnostico Geral

1. **45% dos documentos sao fantasma** (183/402). O pipeline cria registros antes de ter conteudo e nao limpa em caso de falha.

2. **Todos os 64 `prova_respondida` sao null.** Este tipo parece ser usado apenas como marcador de que o aluno submeteu prova, sem armazenar o conteudo no campo `conteudo`.

3. **Redundancia massiva:** Cada execucao do pipeline recria `extracao_questoes` e `extracao_gabarito` da atividade, resultando em 29+27=56 copias de docs base identicos.

4. **3 alunos fantasma** (Alice, Fabricio, Raphael) tem correcoes validas sem prova. Possivelmente tiveram suas provas deletadas depois da correcao, ou foram processados por bug.

5. **10 alunos com prova sem correcao** (nao 7 como estimado). 7 deles estao prontos para correcao imediata. 3 precisam primeiro de extracao de respostas.

6. **Template nao preenchido:** Varios relatorio_final tem `{{nota_final}}` literal -- o template Jinja/Mustache nao foi renderizado antes de salvar.
