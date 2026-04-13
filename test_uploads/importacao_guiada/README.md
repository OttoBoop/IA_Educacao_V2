# Kit de Teste: Importacao Guiada

Use estes arquivos para testar manualmente o novo fluxo de importacao de alunos e upload de provas em lote.

## Tabelas de alunos

- `alunos_importacao_guiada.csv`: tabela limpa, separada por ponto-e-virgula, com cabecalhos diferentes dos nomes internos. Os e-mails sao opcionais e alguns ficam vazios.
- `alunos_importacao_com_problemas.csv`: tabela com uma linha duplicada e uma linha sem nome.
- `alunos_multiplas_abas.xlsx`: planilha com uma aba `Resumo` e uma aba `Alunos 9A`.
- `alunos_multiplas_abas.ods`: versao ODS da mesma ideia.

## Provas

Os PDFs em `provas/` foram nomeados para exercitar a associacao por aluno:

- `prova_A001_Ana_Lima.pdf`: deve sugerir Ana Lima.
- `prova_B002_Bruno_Reis.pdf`: deve sugerir Bruno Reis.
- `prova_C003_Carla_Dias.pdf`: deve sugerir Carla Dias.
- `prova_A001_segunda_tentativa.pdf`: use junto com `prova_A001_Ana_Lima.pdf` para testar bloqueio de duas provas para o mesmo aluno.
- `prova_sem_identificacao.pdf`: deve ficar como "precisa de decisao" ate voce escolher um aluno ou remover do envio.

## Roteiro rapido

1. No modo turmas, abra uma turma de teste.
2. Clique em `Importar Alunos (Tabela)`.
3. Selecione `alunos_importacao_guiada.csv`.
4. Clique em `Analisar Tabela`.
5. Confira os dropdowns:
   - nome -> `nome do aluno`
   - email -> `E-mail institucional` ou vazio, se voce quiser testar importacao sem e-mail
   - matricula -> `RA do estudante` ou vazio, se voce quiser testar importacao sem matricula
6. Clique em `Importar`.
7. Reenvie o mesmo CSV para confirmar que nao duplica alunos.
8. Abra uma atividade dessa turma e clique em `Upload Provas em Lote`.
9. Selecione PDFs da pasta `provas/`.
10. Resolva as linhas pendentes e teste os conflitos antes de enviar.
