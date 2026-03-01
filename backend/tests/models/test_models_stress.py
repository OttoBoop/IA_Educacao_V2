"""
NOVO CR - Teste de Estresse de Modelos v1.0

Testa diferentes modelos da OpenAI com varios parametros
e registra o que funcionou e o que nao funcionou.

Uso:
    cd IA_Educacao_V2/backend
    python test_models.py

Requer:
    - API key OpenAI configurada no sistema (via UI) ou OPENAI_API_KEY no ambiente
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Adicionar diretorio ao path
sys.path.insert(0, str(Path(__file__).parent))

import httpx
from dotenv import load_dotenv

# Carregar .env (se existir)
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)


def get_openai_api_key() -> Optional[str]:
    """Obtém a API key do OpenAI do ambiente ou do armazenamento criptografado"""
    # Primeiro, tentar do ambiente
    key = os.getenv('OPENAI_API_KEY')
    if key:
        return key

    # Se não encontrou, tentar do armazenamento criptografado
    try:
        from chat_service import ApiKeyManager, ProviderType

        manager = ApiKeyManager(str(Path(__file__).parent / "data" / "api_keys.json"))
        for key_config in manager.keys.values():
            if key_config.empresa == ProviderType.OPENAI and key_config.ativo:
                print(f"Usando API key: {key_config.nome_exibicao} ({key_config.id})")
                return key_config.api_key
    except Exception as e:
        print(f"Erro ao carregar do armazenamento criptografado: {e}")

    return None


# Configuracoes
OPENAI_API_KEY = get_openai_api_key()
BASE_URL = "https://api.openai.com/v1"
RESULTS_FILE = Path(__file__).parent / "data" / "test_results.json"

# Modelos para testar (ordenados por custo, mais baratos primeiro)
MODELS_TO_TEST = [
    # Chat models (suportam temperature)
    {
        "id": "gpt-4o-mini",
        "name": "GPT-4o Mini",
        "type": "chat",
        "supports_temperature": True,
        "supports_tools": True,
        "expected_cost": "baixo"
    },
    {
        "id": "gpt-4o",
        "name": "GPT-4o",
        "type": "chat",
        "supports_temperature": True,
        "supports_tools": True,
        "expected_cost": "medio"
    },
    # Reasoning models (usam reasoning_effort)
    {
        "id": "o1",
        "name": "o1",
        "type": "reasoning",
        "supports_temperature": False,
        "supports_tools": True,
        "expected_cost": "alto"
    },
    {
        "id": "o3-mini",
        "name": "o3 Mini",
        "type": "reasoning",
        "supports_temperature": False,
        "supports_tools": True,
        "reasoning_effort": ["low", "medium", "high"],
        "expected_cost": "medio"
    },
]

# Prompts de teste
TEST_PROMPTS = {
    "simple": "Responda em uma linha: Qual e a capital do Brasil?",
    "math": "Calcule: 15 * 23 + 47 - 12. Mostre apenas o resultado.",
    "document": """Gere um JSON com a seguinte estrutura:
{
  "titulo": "Prova de Matematica",
  "questoes": [
    {"numero": 1, "enunciado": "...", "resposta": "..."}
  ]
}
Inclua 2 questoes simples de matematica.""",
}


class ModelTester:
    """Classe para testar modelos de IA"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.results: List[Dict[str, Any]] = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    async def test_model(
        self,
        model_config: Dict[str, Any],
        prompt: str,
        prompt_type: str,
        params_override: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Testa um modelo com um prompt especifico"""
        model_id = model_config["id"]
        is_reasoning = model_config["type"] == "reasoning"

        # Construir parametros
        params = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": "Voce e um assistente util. Seja conciso."},
                {"role": "user", "content": prompt}
            ]
        }

        # Adicionar parametros especificos
        if is_reasoning:
            # Modelos reasoning usam max_completion_tokens e reasoning_effort
            params["max_completion_tokens"] = 1000
            params["reasoning_effort"] = params_override.get("reasoning_effort", "low") if params_override else "low"
        else:
            # Modelos chat usam max_tokens e temperature
            params["max_tokens"] = 1000
            params["temperature"] = params_override.get("temperature", 0.7) if params_override else 0.7

        # Sobrescrever com params_override
        if params_override:
            for key, value in params_override.items():
                if key not in ["reasoning_effort", "temperature"]:  # Ja tratados acima
                    params[key] = value

        result = {
            "model_id": model_id,
            "model_name": model_config["name"],
            "model_type": model_config["type"],
            "prompt_type": prompt_type,
            "params_sent": {k: v for k, v in params.items() if k != "messages"},
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": None,
            "response": None,
            "tokens_used": None,
            "latency_ms": None
        }

        print(f"\n{'='*60}")
        print(f"Testando: {model_config['name']} ({model_id})")
        print(f"Tipo: {model_config['type']}")
        print(f"Prompt: {prompt_type}")
        print(f"Params: {result['params_sent']}")
        print("-" * 60)

        try:
            start_time = datetime.now()

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=params
                )

            latency = (datetime.now() - start_time).total_seconds() * 1000
            result["latency_ms"] = round(latency, 2)

            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                tokens = data.get("usage", {}).get("total_tokens", 0)

                result["success"] = True
                result["response"] = content[:500]  # Limitar tamanho
                result["tokens_used"] = tokens

                print(f"SUCESSO!")
                print(f"Resposta: {content[:200]}...")
                print(f"Tokens: {tokens}")
                print(f"Latencia: {latency:.0f}ms")

            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                result["error"] = {
                    "status_code": response.status_code,
                    "message": str(error_data)[:500]
                }
                print(f"ERRO: {response.status_code}")
                print(f"Detalhes: {error_data}")

        except Exception as e:
            result["error"] = {"exception": str(e)}
            print(f"EXCECAO: {e}")

        self.results.append(result)
        return result

    async def test_tool_use(self, model_config: Dict[str, Any]) -> Dict[str, Any]:
        """Testa tool use / function calling em um modelo"""
        model_id = model_config["id"]

        # Definir uma tool simples
        tools = [{
            "type": "function",
            "function": {
                "name": "create_document",
                "description": "Cria um documento com titulo e conteudo",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "titulo": {
                            "type": "string",
                            "description": "Titulo do documento"
                        },
                        "conteudo": {
                            "type": "string",
                            "description": "Conteudo do documento"
                        }
                    },
                    "required": ["titulo", "conteudo"],
                    "additionalProperties": False
                },
                "strict": True
            }
        }]

        # Parametros
        is_reasoning = model_config["type"] == "reasoning"
        params = {
            "model": model_id,
            "messages": [
                {"role": "system", "content": "Use a funcao create_document para criar documentos quando solicitado."},
                {"role": "user", "content": "Crie um documento com titulo 'Teste' e conteudo 'Este e um teste de tool use'."}
            ],
            "tools": tools,
            "tool_choice": "required"
        }

        if is_reasoning:
            params["max_completion_tokens"] = 1000
            params["reasoning_effort"] = "low"
            # Reasoning models nao suportam parallel_tool_calls
        else:
            params["max_tokens"] = 1000
            params["temperature"] = 0.1  # Baixa para tool use
            params["parallel_tool_calls"] = False  # Apenas para modelos chat

        result = {
            "model_id": model_id,
            "model_name": model_config["name"],
            "model_type": model_config["type"],
            "test_type": "tool_use",
            "timestamp": datetime.now().isoformat(),
            "success": False,
            "error": None,
            "tool_calls": None,
            "latency_ms": None
        }

        print(f"\n{'='*60}")
        print(f"Testando TOOL USE: {model_config['name']}")
        print("-" * 60)

        try:
            start_time = datetime.now()

            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=params
                )

            latency = (datetime.now() - start_time).total_seconds() * 1000
            result["latency_ms"] = round(latency, 2)

            if response.status_code == 200:
                data = response.json()
                message = data["choices"][0]["message"]

                if message.get("tool_calls"):
                    tool_calls = message["tool_calls"]
                    result["success"] = True
                    result["tool_calls"] = [
                        {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"]
                        }
                        for tc in tool_calls
                    ]
                    print(f"SUCESSO! Tool calls: {len(tool_calls)}")
                    for tc in tool_calls:
                        print(f"  - {tc['function']['name']}: {tc['function']['arguments'][:100]}")
                else:
                    result["error"] = {"message": "Modelo nao retornou tool_calls", "content": message.get("content", "")}
                    print(f"FALHOU: Sem tool_calls")
                    print(f"Resposta: {message.get('content', 'N/A')[:200]}")

            else:
                error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                result["error"] = {"status_code": response.status_code, "message": str(error_data)[:500]}
                print(f"ERRO: {response.status_code}")
                print(f"Detalhes: {error_data}")

        except Exception as e:
            result["error"] = {"exception": str(e)}
            print(f"EXCECAO: {e}")

        self.results.append(result)
        return result

    async def run_all_tests(self, skip_expensive: bool = True):
        """Executa todos os testes"""
        print("\n" + "=" * 70)
        print("INICIANDO TESTES DE MODELOS")
        print(f"Session ID: {self.session_id}")
        print(f"Modelos a testar: {len(MODELS_TO_TEST)}")
        print("=" * 70)

        for model in MODELS_TO_TEST:
            if skip_expensive and model.get("expected_cost") == "alto":
                print(f"\n[SKIP] Pulando {model['name']} (custo alto)")
                continue

            # Teste basico
            await self.test_model(model, TEST_PROMPTS["simple"], "simple")

            # Teste de matematica
            await self.test_model(model, TEST_PROMPTS["math"], "math")

            # Teste de geracao de documento
            await self.test_model(model, TEST_PROMPTS["document"], "document")

            # Teste de tool use (se suportado)
            if model.get("supports_tools"):
                await self.test_tool_use(model)

            # Teste de reasoning effort (se for modelo reasoning)
            if model["type"] == "reasoning" and model.get("reasoning_effort"):
                for effort in model["reasoning_effort"]:
                    await self.test_model(
                        model,
                        TEST_PROMPTS["math"],
                        f"reasoning_{effort}",
                        {"reasoning_effort": effort}
                    )

            # Pequena pausa entre modelos
            await asyncio.sleep(1)

    def save_results(self):
        """Salva resultados em arquivo JSON"""
        RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Carregar resultados anteriores se existirem
        all_results = {}
        if RESULTS_FILE.exists():
            try:
                with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
                    all_results = json.load(f)
            except:
                pass

        # Adicionar novos resultados
        all_results[self.session_id] = {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(self.results),
            "successful": len([r for r in self.results if r.get("success")]),
            "failed": len([r for r in self.results if not r.get("success")]),
            "results": self.results
        }

        # Salvar
        with open(RESULTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)

        print(f"\nResultados salvos em: {RESULTS_FILE}")

    def print_summary(self):
        """Imprime resumo dos testes"""
        print("\n" + "=" * 70)
        print("RESUMO DOS TESTES")
        print("=" * 70)

        successful = [r for r in self.results if r.get("success")]
        failed = [r for r in self.results if not r.get("success")]

        print(f"\nTotal de testes: {len(self.results)}")
        print(f"Sucesso: {len(successful)} ({len(successful)/len(self.results)*100:.1f}%)")
        print(f"Falha: {len(failed)} ({len(failed)/len(self.results)*100:.1f}%)")

        if successful:
            print(f"\n{'='*40}")
            print("TESTES BEM-SUCEDIDOS:")
            print("-" * 40)
            for r in successful:
                print(f"  + {r['model_name']} | {r.get('prompt_type', r.get('test_type', 'N/A'))} | {r.get('latency_ms', 0):.0f}ms")

        if failed:
            print(f"\n{'='*40}")
            print("TESTES COM FALHA:")
            print("-" * 40)
            for r in failed:
                error_msg = str(r.get('error', {}).get('message', r.get('error', 'Desconhecido')))[:80]
                print(f"  - {r['model_name']} | {r.get('prompt_type', r.get('test_type', 'N/A'))}")
                print(f"    Erro: {error_msg}")


async def main():
    """Funcao principal"""
    if not OPENAI_API_KEY:
        print("ERRO: OPENAI_API_KEY nao configurada!")
        print("Configure a variavel de ambiente ou adicione ao .env")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("NOVO CR - TESTE DE MODELOS")
    print(f"API Key: {OPENAI_API_KEY[:8]}...{OPENAI_API_KEY[-4:]}")
    print("=" * 70)

    tester = ModelTester(OPENAI_API_KEY)

    try:
        # Executar testes (pular modelos caros por padrao)
        await tester.run_all_tests(skip_expensive=True)
    except KeyboardInterrupt:
        print("\n\nTestes interrompidos pelo usuario.")

    # Salvar e mostrar resumo
    tester.save_results()
    tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main())
