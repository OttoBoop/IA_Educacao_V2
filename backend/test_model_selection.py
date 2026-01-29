"""
Test suite for verifying model selection works correctly in chat and pipeline.
Tests against production API: https://ia-educacao-v2.onrender.com/

This verifies:
1. Chat uses the correct model when model_id is specified
2. Pipeline uses the correct model when model_id is specified
3. Model selection is reflected in the API response
"""
import requests
import time
import json
import sys

BASE_URL = "https://ia-educacao-v2.onrender.com"
TIMEOUT = 120


def print_header(text: str):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print('='*60)


def print_result(name: str, success: bool, details: str = ""):
    status = "PASS" if success else "FAIL"
    color = "\033[92m" if success else "\033[91m"
    reset = "\033[0m"
    print(f"{color}[{status}]{reset} {name}")
    if details:
        for line in details.split('\n'):
            print(f"      {line}")


def get_models():
    """Get all active models from the API"""
    try:
        r = requests.get(f"{BASE_URL}/api/settings/models", timeout=TIMEOUT)
        if r.status_code == 200:
            return [m for m in r.json().get("models", []) if m.get("ativo", True)]
    except Exception as e:
        print(f"Error getting models: {e}")
    return []


def test_chat_model_selection(model: dict) -> tuple[bool, str]:
    """
    Test that chat uses the correct model when model_id is specified.
    The response should contain the model name in the 'modelo' field.
    """
    model_id = model.get("id")
    model_name = model.get("nome")
    expected_modelo = model.get("modelo")

    chat_data = {
        "messages": [{"role": "user", "content": "Diga apenas: teste"}],
        "model_id": model_id
    }

    try:
        r = requests.post(f"{BASE_URL}/api/chat", json=chat_data, timeout=TIMEOUT)

        if r.status_code == 200:
            data = r.json()
            used_model = data.get("modelo", "unknown")

            # Check if the returned model matches what we requested
            if used_model == expected_modelo:
                return True, f"Requested: {expected_modelo}\nUsed: {used_model}"
            else:
                return False, f"MISMATCH!\nRequested: {expected_modelo}\nUsed: {used_model}"
        else:
            error = r.text[:200]
            return False, f"HTTP {r.status_code}: {error}"
    except requests.Timeout:
        return False, "Timeout (120s)"
    except Exception as e:
        return False, f"Exception: {str(e)[:100]}"


def test_pipeline_model_selection() -> dict:
    """
    Test that pipeline uses the correct model.
    Returns results for each model tested.
    """
    print_header("Testing Pipeline Model Selection")

    results = {}

    # First, get turmas and atividades
    try:
        r = requests.get(f"{BASE_URL}/api/turmas", timeout=TIMEOUT)
        turmas = r.json().get("turmas", []) if r.status_code == 200 else []

        if not turmas:
            print("No turmas found - cannot test pipeline")
            return results

        turma_id = turmas[0]["id"]

        r = requests.get(f"{BASE_URL}/api/atividades", params={"turma_id": turma_id}, timeout=TIMEOUT)
        atividades = r.json().get("atividades", []) if r.status_code == 200 else []

        if not atividades:
            print("No atividades found - cannot test pipeline")
            return results

        atividade_id = atividades[0]["id"]

        # Get alunos
        r = requests.get(f"{BASE_URL}/api/alunos", params={"turma_id": turma_id}, timeout=TIMEOUT)
        alunos = r.json().get("alunos", []) if r.status_code == 200 else []

        if not alunos:
            print("No alunos found - cannot test pipeline")
            return results

        aluno_id = alunos[0]["id"]

        print(f"Testing with: turma={turma_id}, atividade={atividade_id}, aluno={aluno_id}")

    except Exception as e:
        print(f"Error getting test data: {e}")
        return results

    # Get models to test (exclude expensive ones like Sonnet)
    models = get_models()
    test_models = [m for m in models if "sonnet" not in m.get("nome", "").lower()]

    print(f"\nTesting {len(test_models)} models in pipeline (excluding Sonnet)")

    for model in test_models[:3]:  # Test only first 3 to save time/cost
        model_id = model.get("id")
        model_name = model.get("nome")
        expected_modelo = model.get("modelo")

        print(f"\n--- Testing: {model_name} ({expected_modelo}) ---")

        # Run pipeline with specific model
        pipeline_data = {
            "atividade_id": atividade_id,
            "aluno_id": aluno_id,
            "model_id": model_id,
            "selected_steps": json.dumps(["extrair_questoes"]),  # Just one step to save time
            "force_rerun": "true"
        }

        try:
            r = requests.post(
                f"{BASE_URL}/api/executar/pipeline-completo",
                data=pipeline_data,
                timeout=180  # Longer timeout for pipeline
            )

            if r.status_code == 200:
                data = r.json()

                # Check the model used in each step
                resultados = data.get("resultados", {})

                for step_name, step_result in resultados.items():
                    used_model = step_result.get("modelo", "unknown")

                    if used_model == expected_modelo:
                        print_result(
                            f"{step_name}",
                            True,
                            f"Model OK: {used_model}"
                        )
                        results[f"{model_name}_{step_name}"] = True
                    else:
                        print_result(
                            f"{step_name}",
                            False,
                            f"MISMATCH! Expected: {expected_modelo}, Got: {used_model}"
                        )
                        results[f"{model_name}_{step_name}"] = False
            else:
                print_result(model_name, False, f"HTTP {r.status_code}: {r.text[:200]}")
                results[model_name] = False

        except requests.Timeout:
            print_result(model_name, False, "Timeout")
            results[model_name] = False
        except Exception as e:
            print_result(model_name, False, str(e)[:100])
            results[model_name] = False

        # Small delay between tests
        time.sleep(2)

    return results


def test_chat_model_selection_all():
    """Test chat model selection for all models"""
    print_header("Testing Chat Model Selection")

    models = get_models()
    if not models:
        print("No models found")
        return {}

    # Exclude expensive models
    test_models = [m for m in models if "sonnet" not in m.get("nome", "").lower()]

    print(f"Testing {len(test_models)} models (excluding Sonnet)\n")

    results = {}

    for model in test_models:
        model_name = model.get("nome")
        print(f"Testing: {model_name}...")

        success, details = test_chat_model_selection(model)
        print_result(model_name, success, details)
        results[model_name] = success

        time.sleep(2)  # Rate limiting

    return results


def main():
    print("="*60)
    print("  Model Selection Verification Tests")
    print(f"  Target: {BASE_URL}")
    print("="*60)

    all_results = {}

    # Test 1: Chat model selection
    chat_results = test_chat_model_selection_all()
    for k, v in chat_results.items():
        all_results[f"chat_{k}"] = v

    # Test 2: Pipeline model selection
    pipeline_results = test_pipeline_model_selection()
    all_results.update(pipeline_results)

    # Summary
    print_header("TEST SUMMARY")

    passed = sum(1 for r in all_results.values() if r is True)
    failed = sum(1 for r in all_results.values() if r is False)

    print("\nChat Tests:")
    for name, result in all_results.items():
        if name.startswith("chat_"):
            status = "PASS" if result else "FAIL"
            color = "\033[92m" if result else "\033[91m"
            reset = "\033[0m"
            print(f"  {color}{status}{reset}: {name.replace('chat_', '')}")

    print("\nPipeline Tests:")
    for name, result in all_results.items():
        if not name.startswith("chat_"):
            status = "PASS" if result else "FAIL"
            color = "\033[92m" if result else "\033[91m"
            reset = "\033[0m"
            print(f"  {color}{status}{reset}: {name}")

    print(f"\nTotal: {passed} passed, {failed} failed")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
