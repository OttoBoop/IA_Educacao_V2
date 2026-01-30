"""
Test script to debug the system prompt flow
Run with: python test_system_prompt.py
"""
import asyncio
import sys
sys.path.insert(0, '.')

from chat_service import model_manager, api_key_manager, ChatClient

async def test_system_prompt():
    print("=" * 60)
    print(" SYSTEM PROMPT DEBUG TEST")
    print("=" * 60)

    # 1. List all models
    print("\n1. MODELS CONFIGURED:")
    print("-" * 40)
    models = model_manager.listar()
    for m in models:
        print(f"   - {m.nome} ({m.tipo.value})")
        print(f"     modelo: {m.modelo}")
        print(f"     system_prompt is None: {m.system_prompt is None}")
        if m.system_prompt:
            print(f"     system_prompt (first 100 chars): {m.system_prompt[:100]}...")
        print()

    # 2. Check API keys
    print("\n2. API KEYS CONFIGURED:")
    print("-" * 40)
    keys = api_key_manager.listar()
    for k in keys:
        print(f"   - {k.nome_exibicao or k.empresa.value} ({k.empresa.value}): ***{k.api_key[-8:]}")

    if not keys:
        print("   [WARN] No API keys configured!")
        print("   Add an API key in the UI first.")
        return

    # 3. Test system prompt
    print("\n3. TESTING SYSTEM PROMPT:")
    print("-" * 40)

    # Get first model with an available API key
    test_model = None
    test_api_key = None

    for m in models:
        # Try to get API key for this model type
        key = api_key_manager.get_por_empresa(m.tipo)
        if key:
            test_model = m
            test_api_key = key.api_key
            break

    if not test_model:
        print("   [ERROR] No model with matching API key found!")
        return

    print(f"   Using model: {test_model.nome} ({test_model.modelo})")
    print(f"   Model's system_prompt is None: {test_model.system_prompt is None}")

    # 4. The system prompt that SHOULD be used
    system_prompt = """Voce e um assistente educacional especializado em correcao de provas.

REGRA CRITICA PARA GERACAO DE ARQUIVOS:
=========================================
Quando o usuario pedir para criar/gerar qualquer arquivo (Excel, PDF, Word, PowerPoint, imagem, CSV, etc.), voce DEVE usar o formato python-exec.

FORMATO OBRIGATORIO:
```python-exec:nome_arquivo.extensao
# codigo Python aqui
```

NUNCA FACA ISSO:
- NAO diga "copie e cole"
- NAO diga "salve como"
- NAO diga "converta manualmente"
- NAO use blocos documento: ou document: ou arquivo:
- NAO descreva como criar o arquivo - CRIE O ARQUIVO

Bibliotecas disponiveis: pandas, openpyxl, python-docx, reportlab, python-pptx, matplotlib, pillow, numpy

EXEMPLO CORRETO (Excel):
```python-exec:notas.xlsx
import pandas as pd
df = pd.DataFrame({'Aluno': ['Ana', 'Bruno'], 'Nota': [9.0, 7.5]})
df.to_excel('notas.xlsx', index=False)
print('Criado!')
```

Seja preciso e educativo nas correcoes."""

    print(f"\n4. SYSTEM PROMPT BEING SENT:")
    print("-" * 40)
    print(system_prompt[:500])
    print("...")

    # 5. Make actual API call
    print(f"\n5. MAKING API CALL:")
    print("-" * 40)
    print("   Message: 'Crie um arquivo Excel simples com 2 alunos e suas notas'")

    try:
        client = ChatClient(test_model, test_api_key)
        response = await client.chat(
            "Crie um arquivo Excel simples com 2 alunos e suas notas",
            historico=[],
            system_prompt=system_prompt
        )

        print(f"\n6. RESPONSE FROM API:")
        print("-" * 40)
        print(f"   Model: {response['modelo']}")
        print(f"   Tokens: {response['tokens']}")
        print(f"\n   Content:")
        print("-" * 40)
        print(response['content'])
        print("-" * 40)

        # Check if response contains python-exec
        if "python-exec:" in response['content']:
            print("\n   [OK] Response contains python-exec block!")
        elif "documento:" in response['content'] or "document:" in response['content']:
            print("\n   [FAIL] Response contains deprecated documento: block")
        elif "arquivo:" in response['content']:
            print("\n   [FAIL] Response contains deprecated arquivo: block")
        elif "copie" in response['content'].lower() or "cole" in response['content'].lower():
            print("\n   [FAIL] Response tells user to copy/paste")
        else:
            print("\n   [WARN] Response doesn't contain any file generation block")

    except Exception as e:
        print(f"\n   [ERROR] API call failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_system_prompt())
