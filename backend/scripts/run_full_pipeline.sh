#!/bin/bash
# Full pipeline: 6 stages × 8 student-activity combos + 7 desempenho reports
# Using Gemini 2.5 Flash Lite (cheapest, fastest)

BASE="https://ia-educacao-v2.onrender.com"
PROVIDER="gem25lite001"
TIMEOUT=300

# Entity IDs from seed_output.json
ATIVIDADES=("f87b6b7e1c3dc5d2" "512a66da87a54f8b" "216476f9c65f96f6" "39ba312d1c3abf33")
TURMA_ALPHA_ALUNOS=("e2b050770435a53a" "8aa3f48d727c5453")
TURMA_BETA_ALUNOS=("a979e6fe03aa1a0b" "45cc242fa25f36c7")
STAGES=("extrair_questoes" "extrair_gabarito" "extrair_respostas" "corrigir" "analisar_habilidades" "gerar_relatorio")

# Atividade 1,2 → Turma Alpha; Atividade 3,4 → Turma Beta
ATIVI_ALUNOS=(
  "f87b6b7e1c3dc5d2:e2b050770435a53a"
  "f87b6b7e1c3dc5d2:8aa3f48d727c5453"
  "512a66da87a54f8b:e2b050770435a53a"
  "512a66da87a54f8b:8aa3f48d727c5453"
  "216476f9c65f96f6:a979e6fe03aa1a0b"
  "216476f9c65f96f6:45cc242fa25f36c7"
  "39ba312d1c3abf33:a979e6fe03aa1a0b"
  "39ba312d1c3abf33:45cc242fa25f36c7"
)

NAMES=(
  "Alpha-Ana-P1" "Alpha-Carlos-P1"
  "Alpha-Ana-P2" "Alpha-Carlos-P2"
  "Beta-Julia-P1" "Beta-Pedro-P1"
  "Beta-Julia-P2" "Beta-Pedro-P2"
)

echo "=== Full Pipeline Run ==="
echo "Provider: $PROVIDER"
echo "Date: $(date)"
echo "Total stages: ${#ATIVI_ALUNOS[@]} × ${#STAGES[@]} = $((${#ATIVI_ALUNOS[@]} * ${#STAGES[@]}))"
echo ""

SUCCESS=0
FAIL=0

for i in "${!ATIVI_ALUNOS[@]}"; do
  IFS=':' read -r ATIVI ALUNO <<< "${ATIVI_ALUNOS[$i]}"
  NAME="${NAMES[$i]}"

  echo "--- $NAME ---"
  for STAGE in "${STAGES[@]}"; do
    RESULT=$(curl -s --max-time $TIMEOUT -X POST "$BASE/api/executar/etapa" \
      -H "Content-Type: application/json" \
      -d "{\"atividade_id\": \"$ATIVI\", \"aluno_id\": \"$ALUNO\", \"etapa\": \"$STAGE\", \"provider\": \"$PROVIDER\"}" 2>&1)

    SUCESSO=$(echo "$RESULT" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('resultado',{}).get('sucesso', False))" 2>/dev/null)
    ERRO=$(echo "$RESULT" | python -c "import sys,json; d=json.load(sys.stdin); e=d.get('resultado',{}).get('erro',''); print(e[:100] if e else '')" 2>/dev/null)

    if [ "$SUCESSO" = "True" ]; then
      echo "  ✓ $STAGE"
      SUCCESS=$((SUCCESS + 1))
    else
      echo "  ✗ $STAGE: $ERRO"
      FAIL=$((FAIL + 1))
      # Skip remaining stages for this student if extraction/correction fails
      if [ "$STAGE" != "gerar_relatorio" ]; then
        echo "  ⏭ Skipping remaining stages for $NAME"
        break
      fi
    fi
  done
  echo ""
done

echo "=== Per-Student Pipeline Results ==="
echo "Success: $SUCCESS | Failed: $FAIL"
echo ""

echo "=== Desempenho Reports ==="

# Tarefa reports (4 atividades)
for ATIVI in "${ATIVIDADES[@]}"; do
  RESULT=$(curl -s --max-time 600 -X POST "$BASE/api/executar/desempenho-tarefa-sync" \
    -F "atividade_id=$ATIVI" 2>&1)
  SUCESSO=$(echo "$RESULT" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('sucesso', False))" 2>/dev/null)
  echo "  Tarefa $ATIVI: $SUCESSO"
done

# Turma reports (2 turmas)
TURMAS=("e7723b846a74d88c" "8ac9388ffc0a6bac")
for TURMA in "${TURMAS[@]}"; do
  RESULT=$(curl -s --max-time 600 -X POST "$BASE/api/executar/desempenho-turma-sync" \
    -F "turma_id=$TURMA" 2>&1)
  SUCESSO=$(echo "$RESULT" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('sucesso', False))" 2>/dev/null)
  echo "  Turma $TURMA: $SUCESSO"
done

# Materia report
MATERIA="9f3e4e15362f3d9e"
RESULT=$(curl -s --max-time 600 -X POST "$BASE/api/executar/desempenho-materia-sync" \
  -F "materia_id=$MATERIA" 2>&1)
SUCESSO=$(echo "$RESULT" | python -c "import sys,json; d=json.load(sys.stdin); print(d.get('sucesso', False))" 2>/dev/null)
echo "  Materia $MATERIA: $SUCESSO"

echo ""
echo "=== DONE ==="
echo "Per-student: $SUCCESS succeeded, $FAIL failed"
