"""
Test the actual /api/chat endpoint
Run with: python test_endpoint.py

Make sure the server is running first: python main_v2.py
"""
import asyncio
import httpx

async def test_chat_endpoint():
    print("=" * 60)
    print(" TESTING /api/chat ENDPOINT")
    print("=" * 60)

    # First, get the list of models to find one we can use
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("\n1. Getting models list...")
        try:
            response = await client.get("http://localhost:8000/api/settings/models")
            if response.status_code != 200:
                print(f"   [ERROR] Failed to get models: {response.status_code}")
                print(f"   Response: {response.text}")
                return

            models = response.json()
            print(f"   Found {len(models.get('models', []))} models")

            if not models.get('models'):
                print("   [ERROR] No models configured!")
                return

            # Use the first model
            model_id = models['models'][0]['id']
            model_name = models['models'][0]['nome']
            print(f"   Using: {model_name} ({model_id})")
        except Exception as e:
            print(f"   [ERROR] {e}")
            print("   Make sure the server is running: python main_v2.py")
            return

        print("\n2. Sending chat request...")
        print("   Message: 'Crie um arquivo Excel simples com 2 alunos e suas notas'")

        try:
            response = await client.post(
                "http://localhost:8000/api/chat",
                json={
                    "messages": [
                        {"role": "user", "content": "Crie um arquivo Excel simples com 2 alunos e suas notas"}
                    ],
                    "model_id": model_id
                }
            )

            print(f"\n3. Response status: {response.status_code}")

            if response.status_code != 200:
                print(f"   [ERROR] Request failed")
                print(f"   Response: {response.text[:500]}")
                return

            data = response.json()

            print(f"\n4. Response data:")
            print(f"   - model: {data.get('model')}")
            print(f"   - model_name: {data.get('model_name')}")
            print(f"   - tokens_used: {data.get('tokens_used')}")
            print(f"   - latency_ms: {data.get('latency_ms')}")
            print(f"   - debug_endpoint: {data.get('debug_endpoint', 'NOT PRESENT')}")
            print(f"   - debug_prompt_start: {data.get('debug_prompt_start', 'NOT PRESENT')}")

            # Check for debug marker in response
            content = data.get('response', '')
            if "DEBUG_V3_MARKER_2026" in content:
                print(f"   - DEBUG MARKER: FOUND (code v3 is running!)")
            else:
                print(f"   - DEBUG MARKER: NOT FOUND (old code running?)")

            print(f"\n5. Response content:")
            print("-" * 40)
            print(content)
            print("-" * 40)

            # Analyze the response
            print("\n6. Analysis:")
            if "python-exec:" in content:
                print("   [OK] Response contains python-exec: block!")
            elif "documento-binario:" in content:
                print("   [OK] Response contains documento-binario: block (file was generated!)")
            elif "documento:" in content or "document:" in content:
                print("   [FAIL] Response contains deprecated documento:/document: block")
            elif "arquivo:" in content:
                print("   [FAIL] Response contains deprecated arquivo: block")
            elif "copie" in content.lower() or "cole" in content.lower():
                print("   [FAIL] Response tells user to copy/paste")
            elif "salve" in content.lower() and "como" in content.lower():
                print("   [FAIL] Response tells user to save as")
            else:
                print("   [WARN] Response doesn't contain any recognized file generation block")

        except Exception as e:
            print(f"   [ERROR] Request failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_chat_endpoint())
