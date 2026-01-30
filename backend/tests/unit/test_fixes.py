"""
Test suite for verifying bug fixes in IA_Educacao_V2
Tests against production API: https://ia-educacao-v2.onrender.com/

Run with: python test_fixes.py
"""
import requests
import time
import sys

BASE_URL = "https://ia-educacao-v2.onrender.com"
TIMEOUT = 120  # Render can be slow on cold starts


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
        print(f"      {details}")


def get_models():
    """Get all configured models from the API"""
    try:
        r = requests.get(f"{BASE_URL}/api/settings/models", timeout=TIMEOUT)
        if r.status_code == 200:
            return r.json().get("models", [])
    except Exception as e:
        print(f"Error getting models: {e}")
    return []


def _check_model_chat(model: dict) -> tuple[bool, str]:
    """Check chat functionality for a specific model (helper, not a pytest test)"""
    model_id = model.get("id")
    model_name = model.get("nome", model_id)
    model_tipo = model.get("tipo", "unknown")

    chat_data = {
        "messages": [{"role": "user", "content": "Responda apenas: OK"}],
        "model_id": model_id
    }

    try:
        r = requests.post(f"{BASE_URL}/api/chat", json=chat_data, timeout=TIMEOUT)

        if r.status_code == 200:
            response = r.json().get("response", "")
            preview = response[:50] + "..." if len(response) > 50 else response
            return True, f"Response: {preview}"
        else:
            error = r.text[:200]
            return False, f"HTTP {r.status_code}: {error}"
    except requests.Timeout:
        return False, "Timeout (120s)"
    except Exception as e:
        return False, f"Exception: {str(e)[:100]}"


def test_all_models():
    """Test all configured models"""
    print_header("Testing All Configured Models")

    models = get_models()
    if not models:
        print("No models found or API unavailable")
        return {}

    print(f"Found {len(models)} model(s) configured\n")

    results = {}

    # Group models by provider
    by_provider = {}
    for m in models:
        provider = m.get("tipo", "unknown")
        if provider not in by_provider:
            by_provider[provider] = []
        by_provider[provider].append(m)

    for provider, provider_models in by_provider.items():
        print(f"\n--- {provider.upper()} ---")

        for model in provider_models:
            model_name = model.get("nome", model.get("id"))
            model_id = model.get("modelo", "")

            print(f"\nTesting: {model_name} ({model_id})")

            success, details = _check_model_chat(model)
            print_result(model_name, success, details)

            results[model_name] = success

            # Small delay between requests to avoid rate limiting
            time.sleep(2)

    return results


def test_document_integrity():
    """Test document storage integrity"""
    print_header("Testing Document Storage Integrity")

    try:
        # Get turmas
        r = requests.get(f"{BASE_URL}/api/turmas", timeout=TIMEOUT)
        if r.status_code != 200:
            print("Could not get turmas")
            return None

        turmas = r.json().get("turmas", [])
        if not turmas:
            print("No turmas found - skipping test")
            return None

        # Get atividades from first turma
        turma_id = turmas[0].get("id")
        r = requests.get(f"{BASE_URL}/api/atividades", params={"turma_id": turma_id}, timeout=TIMEOUT)
        if r.status_code != 200:
            print("Could not get atividades")
            return None

        atividades = r.json().get("atividades", [])
        if not atividades:
            print("No atividades found - skipping test")
            return None

        # Test integrity endpoint
        atividade_id = atividades[0].get("id")
        r = requests.get(
            f"{BASE_URL}/api/documentos/verificar-integridade",
            params={"atividade_id": atividade_id},
            timeout=TIMEOUT
        )

        if r.status_code == 404:
            print("Integrity endpoint not deployed yet")
            return None
        elif r.status_code == 200:
            data = r.json()
            total = data.get("total", 0)
            com_arquivo = data.get("com_arquivo", 0)
            sem_arquivo = data.get("sem_arquivo", 0)

            print(f"Total documents in DB: {total}")
            print(f"With file on disk: {com_arquivo}")
            print(f"Missing file: {sem_arquivo}")

            if sem_arquivo > 0:
                print("\nWARNING: Some documents have missing files")
                print("This is expected on Render.com due to ephemeral storage")
                return False
            return True
        else:
            print(f"Unexpected response: HTTP {r.status_code}")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return None


def test_model_configuration():
    """Verify model configurations are correct"""
    print_header("Verifying Model Configurations")

    models = get_models()
    if not models:
        print("No models found")
        return {}

    results = {}

    # Check Claude Haiku model ID
    haiku_models = [m for m in models if "haiku" in m.get("nome", "").lower()]
    for m in haiku_models:
        model_id = m.get("modelo", "")
        expected = "claude-haiku-4-5-20251001"
        is_correct = model_id == expected
        print_result(
            f"Claude Haiku model ID",
            is_correct,
            f"Got '{model_id}', expected '{expected}'"
        )
        results["haiku_config"] = is_correct

    # Check Gemini doesn't have reasoning_effort
    gemini_models = [m for m in models if m.get("tipo") == "google"]
    for m in gemini_models:
        params = m.get("parametros", {})
        has_reasoning_effort = "reasoning_effort" in params
        is_correct = not has_reasoning_effort
        print_result(
            f"Gemini '{m.get('nome')}' parametros",
            is_correct,
            f"reasoning_effort present: {has_reasoning_effort} (should be False)"
        )
        results["gemini_config"] = is_correct

    return results


def main():
    print("="*60)
    print("  IA_Educacao_V2 Bug Fix Verification Tests")
    print(f"  Target: {BASE_URL}")
    print("="*60)

    all_results = {}

    # Test 1: Model configurations
    config_results = test_model_configuration()
    all_results.update(config_results)

    # Test 2: All model chat functionality
    chat_results = test_all_models()
    all_results.update(chat_results)

    # Test 3: Document integrity
    integrity_result = test_document_integrity()
    if integrity_result is not None:
        all_results["document_integrity"] = integrity_result

    # Summary
    print_header("TEST SUMMARY")

    passed = sum(1 for r in all_results.values() if r is True)
    failed = sum(1 for r in all_results.values() if r is False)

    for name, result in all_results.items():
        status = "PASS" if result else "FAIL"
        color = "\033[92m" if result else "\033[91m"
        reset = "\033[0m"
        print(f"  {color}{status}{reset}: {name}")

    print(f"\nTotal: {passed} passed, {failed} failed")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
