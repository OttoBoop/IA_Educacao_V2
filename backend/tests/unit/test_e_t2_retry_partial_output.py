"""
Test E-T2: Retry logic for partial dual-output in executar_com_tools()

Tests:
1. test_both_outputs_produced_no_retry
   When tool_calls contains both create_document AND execute_python_code, no retry
   happens — chat_with_tools is called exactly once.

2. test_only_json_triggers_retry
   Only create_document in tool_calls → retry triggered. A second call to
   chat_with_tools must happen and the follow-up message must mention PDF/código.

3. test_only_pdf_triggers_retry
   Only execute_python_code in tool_calls → retry triggered. A second call to
   chat_with_tools must happen and the follow-up message must mention JSON/documento.

4. test_retry_succeeds_both_outputs_produced
   First call: only create_document. Retry call: both create_document AND
   execute_python_code → sucesso=True, tentativas=2.

5. test_retry_fails_partial_saved_with_warning
   Both calls produce only create_document → result is sucesso=False; partial
   output is not accepted as completed.

6. test_single_tool_in_tools_to_use_no_dual_check
   When tools_to_use=["create_document"] only (no execute_python_code), the
   dual-output check must NOT apply — no retry even if execute_python_code is absent.

Root cause these tests guard against:
  executor.py lines ~1839-1869 call chat_with_tools exactly once and return
  immediately. There is no check for whether both create_document AND
  execute_python_code appear in tool_calls. Tests 2/3/4/5 will fail because
  the second call never happens, and test 4 will fail because tentativas==1.

Run: cd IA_Educacao_V2/backend && pytest tests/unit/test_e_t2_retry_partial_output.py -v
"""

import pytest
import sys
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, AsyncMock, patch, call

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from executor import PipelineExecutor, ResultadoExecucao, EtapaProcessamento
from models import StatusProcessamento, TipoDocumento


# ============================================================
# RESPONSE FACTORIES
# ============================================================

def _tool_response(tool_names: list[str]) -> dict:
    """Build a chat_with_tools response dict containing the specified tool names."""
    tool_calls = []
    for name in tool_names:
        if name == "create_document":
            tool_calls.append({
                "name": "create_document",
                "input": {
                    "documents": [
                        {"filename": "relatorio_aluno.json", "content": "{}"}
                    ]
                },
            })
        elif name == "execute_python_code":
            tool_calls.append({
                "name": "execute_python_code",
                "input": {"code": "# generate PDF\nprint('done')"},
            })

    return {
        "content": "Relatório gerado com sucesso.",
        "tokens": 150,
        "modelo": "test-model",
        "provider": "anthropic",
        "tool_calls": tool_calls,
    }


def _tool_response_with_json_content(content: dict) -> dict:
    """Build a dual-output response whose JSON content can be schema-validated."""
    return {
        "content": "",
        "input_tokens": 40,
        "output_tokens": 12,
        "modelo": "test-model",
        "provider": "anthropic",
        "tool_calls": [
            {
                "name": "create_document",
                "input": {
                    "documents": [
                        {
                            "filename": "relatorio_aluno.json",
                            "content": json.dumps(content),
                        }
                    ]
                },
            },
            {
                "name": "execute_python_code",
                "input": {"code": "# generate PDF\nprint('done')"},
            },
        ],
    }


def _make_mock_model(suporta_function_calling: bool = True, tipo_value: str = "anthropic"):
    """Build a minimal ModelConfig-like mock."""
    model = MagicMock()
    model.suporta_function_calling = suporta_function_calling
    model.tipo = MagicMock()
    model.tipo.value = tipo_value
    model.modelo = "claude-haiku-test"
    model.api_key_id = ""
    return model


def _make_chat_service_module(model, chat_with_tools_side_effect):
    """
    Build a mock chat_service module.

    chat_with_tools_side_effect must be a list of return values (one per call)
    or a single return value.  We use AsyncMock with side_effect so we can
    track multiple sequential calls (first call / retry call).
    """
    mock_module = MagicMock()

    mock_manager = MagicMock()
    mock_manager.get = MagicMock(return_value=model)
    mock_manager.get_default = MagicMock(return_value=model)
    mock_module.model_manager = mock_manager

    mock_key_manager = MagicMock()
    api_key_config = MagicMock()
    api_key_config.api_key = "test-api-key-abc"
    mock_key_manager.get = MagicMock(return_value=None)
    mock_key_manager.get_por_empresa = MagicMock(return_value=api_key_config)
    mock_module.api_key_manager = mock_key_manager

    from chat_service import ProviderType
    mock_module.ProviderType = ProviderType
    mock_module.ProviderAPIError = Exception

    mock_client_instance = MagicMock()

    # Build the side_effect list for AsyncMock
    if isinstance(chat_with_tools_side_effect, list):
        mock_client_instance.chat_with_tools = AsyncMock(
            side_effect=chat_with_tools_side_effect
        )
    else:
        # Single return value — only one call expected
        mock_client_instance.chat_with_tools = AsyncMock(
            return_value=chat_with_tools_side_effect
        )

    mock_client_instance.chat = AsyncMock(return_value={
        "content": "Fallback text",
        "tokens": 10,
        "modelo": "test-model",
        "provider": "anthropic",
    })

    mock_chat_client_cls = MagicMock(return_value=mock_client_instance)
    mock_module.ChatClient = mock_chat_client_cls

    return mock_module, mock_client_instance


def _make_tools_module():
    """Build a minimal tools module mock."""
    mock_module = MagicMock()
    mock_module.ToolRegistry = MagicMock(return_value=MagicMock())

    class FakeTool:
        def __init__(self, name):
            self.name = name
            self.handler = None

        def to_anthropic_format(self):
            properties = {}
            if self.name == "create_document":
                properties["documents"] = {
                    "type": "array",
                    "description": "Fake documents",
                    "items": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string"},
                            "content": {"type": "string"},
                        },
                    },
                }
            return {
                "name": self.name,
                "description": f"Fake {self.name}",
                "input_schema": {"type": "object", "properties": properties, "required": []},
            }

    create_document = FakeTool("create_document")
    execute_python_code = FakeTool("execute_python_code")

    mock_module.PIPELINE_TOOLS = [create_document, execute_python_code]
    mock_module.CREATE_DOCUMENT = create_document
    mock_module.EXECUTE_PYTHON_CODE = execute_python_code

    class FakeToolExecutionContext:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            self.created_document_ids = []

    mock_module.ToolExecutionContext = FakeToolExecutionContext
    return mock_module


def _make_tool_handlers_module():
    """Build a minimal tool_handlers module mock."""
    mock_module = MagicMock()
    mock_module.TOOL_HANDLERS = {}
    return mock_module


async def _call_executar_com_tools(
    chat_side_effect,
    tools_to_use=None,
    provider_id=None,
    tipo_value="anthropic",
    expected_document_type=None,
):
    """
    Patch lazy-imported modules and call executar_com_tools.

    chat_side_effect: list of dicts (one per chat_with_tools call) OR a single dict.
    Returns: (ResultadoExecucao, mock_client_instance)
    """
    model = _make_mock_model(suporta_function_calling=True, tipo_value=tipo_value)
    chat_service_mock, mock_client = _make_chat_service_module(model, chat_side_effect)
    tools_mock = _make_tools_module()
    tool_handlers_mock = _make_tool_handlers_module()

    with patch.dict(
        "sys.modules",
        {
            "chat_service": chat_service_mock,
            "tools": tools_mock,
            "tool_handlers": tool_handlers_mock,
        },
    ):
        executor = PipelineExecutor()
        result = await executor.executar_com_tools(
            mensagem="Gere o relatório completo do aluno.",
            atividade_id="atividade_test_et2",
            aluno_id="aluno_test_et2",
            provider_id=provider_id,
            tools_to_use=tools_to_use,
            expected_document_type=expected_document_type,
        )

    return result, mock_client


# ============================================================
# TEST 1: Both outputs produced → no retry
# ============================================================

class TestBothOutputsNoRetry:
    """When tool_calls contains both create_document and execute_python_code,
    no retry should happen — chat_with_tools must be called exactly once."""

    async def test_both_outputs_produced_no_retry(self):
        """Both create_document AND execute_python_code present → single call, no retry.

        This test should PASS immediately (no retry needed when both outputs exist).
        It is the baseline / control case.
        """
        both_response = _tool_response(["create_document", "execute_python_code"])
        result, mock_client = await _call_executar_com_tools(
            chat_side_effect=both_response,
            tools_to_use=["create_document", "execute_python_code"],
        )

        assert isinstance(result, ResultadoExecucao)
        assert result.sucesso is True, (
            f"Both outputs present → expected sucesso=True, got sucesso={result.sucesso}"
        )

    async def test_expected_document_type_returns_real_stage_and_parsed_json(self):
        """Tool-use success should return the pipeline stage and parsed JSON."""
        json_content = {
            "nota_final": 3,
            "questoes": [{"numero": 1, "nota": 3, "acerto": True, "feedback": "Correto"}],
            "total_acertos": 1,
            "total_erros": 0,
            "feedback_geral": "Bom desempenho",
            "_avisos_documento": [],
            "_avisos_questao": [],
        }
        response = {
            "content": "",
            "tokens": 150,
            "modelo": "test-model",
            "provider": "anthropic",
            "tool_calls": [
                {
                    "name": "create_document",
                    "input": {
                        "documents": [
                            {
                                "filename": "correcao.json",
                                "content": json.dumps(json_content),
                            }
                        ]
                    },
                },
                {
                    "name": "execute_python_code",
                    "input": {"code": "# generate PDF"},
                },
            ],
        }

        result, mock_client = await _call_executar_com_tools(
            chat_side_effect=response,
            tools_to_use=["create_document", "execute_python_code"],
            expected_document_type=TipoDocumento.CORRECAO,
        )

        assert result.sucesso is True
        assert result.etapa == EtapaProcessamento.CORRIGIR
        assert result.resposta_parsed == json_content

        call_count = mock_client.chat_with_tools.call_count
        assert call_count == 1, (
            f"Both outputs present → chat_with_tools should be called exactly ONCE "
            f"(no retry needed). Got call_count={call_count}."
        )

    async def test_expected_document_type_rejects_runtime_json_outside_schema(self):
        """Parseable create_document JSON outside the stage schema must fail high."""
        response = {
            "content": "",
            "tokens": 150,
            "modelo": "test-model",
            "provider": "anthropic",
            "tool_calls": [
                {
                    "name": "create_document",
                    "input": {
                        "documents": [
                            {
                                "filename": "correcao.json",
                                "content": json.dumps({"feedback_geral": "sem dados"}),
                            }
                        ]
                    },
                },
                {
                    "name": "execute_python_code",
                    "input": {"code": "# generate PDF"},
                },
            ],
        }

        result, _mock_client = await _call_executar_com_tools(
            chat_side_effect=response,
            tools_to_use=["create_document", "execute_python_code"],
            expected_document_type=TipoDocumento.CORRECAO,
        )

        assert result.sucesso is False
        assert "sem nota_final" in (result.erro or "")
        assert "sem lista de questoes" in (result.erro or "")

    @pytest.mark.parametrize(
        ("document_type", "filename", "payload", "expected_error"),
        [
            (
                TipoDocumento.ANALISE_HABILIDADES,
                "analise_habilidades.json",
                {"resumo_geral": "texto sem habilidades"},
                "sem lista/dicionário de habilidades",
            ),
            (
                TipoDocumento.ANALISE_HABILIDADES,
                "analise_habilidades.json",
                {
                    "habilidades": [
                        {
                            "nome": "Operações com frações",
                            "nivel": "adequado",
                            "evidencias": ["Resolveu 3 de 4 questões."],
                            "nota": 8,
                        }
                    ],
                    "indicadores": {
                        "proficiencia_geral": 80,
                        "areas_destaque": ["adição"],
                        "areas_atencao": ["porcentagem"],
                    },
                    "recomendacoes": [],
                },
                "sem _avisos_documento como lista",
            ),
            (
                TipoDocumento.RELATORIO_FINAL,
                "relatorio_final.json",
                {"resumo_geral": "texto sem nota"},
                "sem nota_final",
            ),
            (
                TipoDocumento.RELATORIO_FINAL,
                "relatorio_final.json",
                {
                    "resumo_geral": "Diana teve bom desempenho geral.",
                    "pontos_fortes": ["Organização"],
                    "areas_melhoria": ["Porcentagens"],
                    "recomendacoes": [],
                    "nota_final": 8,
                    "detalhamento": "Errou apenas a questão de porcentagem.",
                    "_avisos_documento": [],
                    "_avisos_questao": [],
                },
                "sem _fontes_utilizadas como lista",
            ),
        ],
    )
    async def test_expected_document_type_rejects_runtime_json_outside_schema_for_late_stages(
        self,
        document_type,
        filename,
        payload,
        expected_error,
    ):
        """ANALISAR/RELATORIO runtime JSON must also obey stage schema."""
        response = {
            "content": "",
            "tokens": 150,
            "modelo": "test-model",
            "provider": "anthropic",
            "tool_calls": [
                {
                    "name": "create_document",
                    "input": {
                        "documents": [
                            {
                                "filename": filename,
                                "content": json.dumps(payload),
                            }
                        ]
                    },
                },
                {
                    "name": "execute_python_code",
                    "input": {"code": "# generate PDF"},
                },
            ],
        }

        result, _mock_client = await _call_executar_com_tools(
            chat_side_effect=response,
            tools_to_use=["create_document", "execute_python_code"],
            expected_document_type=document_type,
        )

        assert result.sucesso is False
        assert expected_error in (result.erro or "")

    async def test_openai_dual_output_starts_with_forced_json_tool_choice(self):
        """OpenAI dual-output calls should force create_document upfront."""
        both_response = _tool_response(["create_document", "execute_python_code"])
        _result, mock_client = await _call_executar_com_tools(
            chat_side_effect=both_response,
            tools_to_use=["create_document", "execute_python_code"],
            tipo_value="openai",
        )

        first_call = mock_client.chat_with_tools.call_args_list[0]
        assert first_call.kwargs.get("tool_choice") == {
            "type": "function",
            "function": {"name": "create_document"},
        }
        first_tool_names = [tool["name"] for tool in first_call.kwargs["tools"]]
        assert first_tool_names == ["create_document"]

    async def test_google_dual_output_starts_with_forced_json_tool_choice(self):
        """Google dual-output calls should also force create_document upfront."""
        both_response = _tool_response(["create_document", "execute_python_code"])
        _result, mock_client = await _call_executar_com_tools(
            chat_side_effect=both_response,
            tools_to_use=["create_document", "execute_python_code"],
            tipo_value="google",
        )

        first_call = mock_client.chat_with_tools.call_args_list[0]
        assert first_call.kwargs.get("tool_choice") == {
            "type": "function",
            "function": {"name": "create_document"},
        }
        first_tool_names = [tool["name"] for tool in first_call.kwargs["tools"]]
        assert first_tool_names == ["create_document"]

    async def test_openai_initial_message_requests_create_document_only(self):
        """The first OpenAI dual-output request must align the prompt with the exposed tool."""
        both_response = _tool_response(["create_document", "execute_python_code"])
        _result, mock_client = await _call_executar_com_tools(
            chat_side_effect=both_response,
            tools_to_use=["create_document", "execute_python_code"],
            tipo_value="openai",
        )

        first_message = mock_client.chat_with_tools.call_args_list[0].kwargs["mensagem"].lower()
        assert "primeira chamada" in first_message
        assert "create_document" in first_message
        assert "exatamente um arquivo .json" in first_message
        assert "nao responda em texto simples" in first_message
        assert "execute_python_code" in first_message

    async def test_pipeline_create_document_description_restricts_to_json(self):
        """Pipeline create_document schema must not advertise PDF creation."""
        both_response = _tool_response(["create_document", "execute_python_code"])
        _result, mock_client = await _call_executar_com_tools(
            chat_side_effect=both_response,
            tools_to_use=["create_document", "execute_python_code"],
            tipo_value="openai",
            expected_document_type=TipoDocumento.CORRECAO,
        )

        first_call = mock_client.chat_with_tools.call_args_list[0]
        create_doc_tool = first_call.kwargs["tools"][0]
        description = create_doc_tool["description"].lower()
        docs_description = (
            create_doc_tool["input_schema"]["properties"]["documents"]["description"].lower()
        )

        assert ".json" in description
        assert "only" in description
        assert "do not use create_document for pdf" in description
        assert ".json" in docs_description

    async def test_pipeline_create_document_content_schema_accepts_json_object(self):
        """Pipeline JSON artifacts should not force nested JSON content into a string."""
        both_response = _tool_response(["create_document", "execute_python_code"])
        _result, mock_client = await _call_executar_com_tools(
            chat_side_effect=both_response,
            tools_to_use=["create_document", "execute_python_code"],
            tipo_value="openai",
            expected_document_type=TipoDocumento.ANALISE_HABILIDADES,
        )

        create_doc_tool = mock_client.chat_with_tools.call_args_list[0].kwargs["tools"][0]
        content_schema = (
            create_doc_tool["input_schema"]["properties"]["documents"]["items"]
            ["properties"]["content"]
        )

        assert {"type": "object"} in content_schema["anyOf"]
        assert {"type": "array", "items": {}} in content_schema["anyOf"]
        assert {"type": "string"} in content_schema["anyOf"]
        assert "prefer passing an object" in content_schema["description"].lower()

    async def test_openai_no_tools_retries_with_forced_json_tool_choice(self):
        """If OpenAI still returns plain text, retry must force create_document again."""
        no_tools_response = _tool_response([])
        retry_response = _tool_response(["create_document", "execute_python_code"])

        result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[no_tools_response, retry_response],
            tools_to_use=["create_document", "execute_python_code"],
            tipo_value="openai",
        )

        assert result.sucesso is True
        assert mock_client.chat_with_tools.call_count == 2
        second_call = mock_client.chat_with_tools.call_args_list[1]
        assert second_call.kwargs.get("tool_choice") == {
            "type": "function",
            "function": {"name": "create_document"},
        }
        second_tool_names = [tool["name"] for tool in second_call.kwargs["tools"]]
        assert second_tool_names == ["create_document"]

    async def test_openai_no_tools_can_retry_json_then_pdf(self):
        """OpenAI may need a JSON repair call before the PDF call."""
        no_tools_response = _tool_response([])
        json_response = _tool_response(["create_document"])
        pdf_response = _tool_response(["execute_python_code"])

        result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[no_tools_response, json_response, pdf_response],
            tools_to_use=["create_document", "execute_python_code"],
            tipo_value="openai",
        )

        assert result.sucesso is True
        assert result.tentativas == 3
        assert mock_client.chat_with_tools.call_count == 3
        second_tool_names = [
            tool["name"]
            for tool in mock_client.chat_with_tools.call_args_list[1].kwargs["tools"]
        ]
        third_tool_names = [
            tool["name"]
            for tool in mock_client.chat_with_tools.call_args_list[2].kwargs["tools"]
        ]
        assert second_tool_names == ["create_document"]
        assert third_tool_names == ["execute_python_code"]
        assert mock_client.chat_with_tools.call_args_list[1].kwargs["tool_choice"] == {
            "type": "function",
            "function": {"name": "create_document"},
        }
        assert mock_client.chat_with_tools.call_args_list[2].kwargs["tool_choice"] == {
            "type": "function",
            "function": {"name": "execute_python_code"},
        }

    async def test_google_no_tools_can_retry_json_then_pdf(self):
        """Google may need a forced JSON call before a forced PDF call."""
        no_tools_response = _tool_response([])
        json_response = _tool_response(["create_document"])
        pdf_response = _tool_response(["execute_python_code"])

        result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[no_tools_response, json_response, pdf_response],
            tools_to_use=["create_document", "execute_python_code"],
            tipo_value="google",
        )

        assert result.sucesso is True
        assert result.tentativas == 3
        assert mock_client.chat_with_tools.call_count == 3
        second_tool_names = [
            tool["name"]
            for tool in mock_client.chat_with_tools.call_args_list[1].kwargs["tools"]
        ]
        third_tool_names = [
            tool["name"]
            for tool in mock_client.chat_with_tools.call_args_list[2].kwargs["tools"]
        ]
        assert second_tool_names == ["create_document"]
        assert third_tool_names == ["execute_python_code"]
        assert mock_client.chat_with_tools.call_args_list[1].kwargs["tool_choice"] == {
            "type": "function",
            "function": {"name": "create_document"},
        }
        assert mock_client.chat_with_tools.call_args_list[2].kwargs["tool_choice"] == {
            "type": "function",
            "function": {"name": "execute_python_code"},
        }

    async def test_openai_only_json_retry_exposes_only_pdf_tool(self):
        """When JSON exists, the repair call should expose only execute_python_code."""
        only_json_response = _tool_response(["create_document"])
        retry_response = _tool_response(["create_document", "execute_python_code"])

        result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[only_json_response, retry_response],
            tools_to_use=["create_document", "execute_python_code"],
            tipo_value="openai",
        )

        assert result.sucesso is True
        second_call = mock_client.chat_with_tools.call_args_list[1]
        tool_names = [tool["name"] for tool in second_call.kwargs["tools"]]
        assert tool_names == ["execute_python_code"]
        assert second_call.kwargs.get("tool_choice") == {
            "type": "function",
            "function": {"name": "execute_python_code"},
        }

    async def test_openai_only_pdf_retry_exposes_only_json_tool(self):
        """When PDF exists, the repair call should expose only create_document."""
        only_pdf_response = _tool_response(["execute_python_code"])
        retry_response = _tool_response(["create_document", "execute_python_code"])

        result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[only_pdf_response, retry_response],
            tools_to_use=["create_document", "execute_python_code"],
            tipo_value="openai",
        )

        assert result.sucesso is True
        second_call = mock_client.chat_with_tools.call_args_list[1]
        tool_names = [tool["name"] for tool in second_call.kwargs["tools"]]
        assert tool_names == ["create_document"]
        assert second_call.kwargs.get("tool_choice") == {
            "type": "function",
            "function": {"name": "create_document"},
        }


# ============================================================
# TEST 2: Only JSON → retry with PDF mention
# ============================================================

class TestOnlyJsonTriggersRetry:
    """When only create_document appears in tool_calls (no execute_python_code),
    a second call to chat_with_tools must happen and the follow-up message
    must mention PDF or código."""

    async def test_only_json_triggers_retry(self):
        """Only create_document called → retry triggered.

        Currently FAILS: chat_with_tools is called once and returns immediately.
        After E-T2 the executor must detect missing execute_python_code and retry.
        """
        only_json_response = _tool_response(["create_document"])
        # Provide two responses: first call (only JSON), second call (retry — irrelevant content)
        retry_response = _tool_response(["create_document", "execute_python_code"])

        result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[only_json_response, retry_response],
            tools_to_use=["create_document", "execute_python_code"],
        )

        call_count = mock_client.chat_with_tools.call_count
        assert call_count == 2, (
            f"Only create_document in first response → retry expected. "
            f"chat_with_tools should be called TWICE (original + retry). "
            f"Got call_count={call_count}. "
            "Current code calls once and returns — this is the bug E-T2 must fix."
        )

    async def test_only_json_retry_message_mentions_pdf(self):
        """The retry follow-up message must reference PDF or código so the model
        knows what to generate on the second attempt.

        Currently FAILS: no second call exists, so no follow-up message is sent.
        """
        only_json_response = _tool_response(["create_document"])
        retry_response = _tool_response(["create_document", "execute_python_code"])

        _result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[only_json_response, retry_response],
            tools_to_use=["create_document", "execute_python_code"],
        )

        call_count = mock_client.chat_with_tools.call_count
        assert call_count == 2, (
            f"Retry call expected but got call_count={call_count}."
        )

        # Inspect the second call's mensagem argument
        second_call_kwargs = mock_client.chat_with_tools.call_args_list[1]
        # Accept both positional and keyword forms
        mensagem_retry = (
            second_call_kwargs.kwargs.get("mensagem")
            or (second_call_kwargs.args[0] if second_call_kwargs.args else None)
        )

        assert mensagem_retry is not None, (
            "Second (retry) call to chat_with_tools must receive a mensagem argument."
        )

        mensagem_lower = mensagem_retry.lower()
        has_pdf_ref = any(
            keyword in mensagem_lower
            for keyword in ["pdf", "código", "codigo", "execute_python_code", "python"]
        )
        assert has_pdf_ref, (
            f"Retry message must mention PDF/código so the model knows what to create. "
            f"Got mensagem_retry={mensagem_retry!r}"
        )

    async def test_only_json_retry_message_preserves_original_context(self):
        """The PDF repair retry must include the original task context.

        Small reasoning models can otherwise invent placeholders such as
        student123 when the retry only says "make the missing PDF".
        """
        only_json_response = _tool_response(["create_document"])
        retry_response = _tool_response(["create_document", "execute_python_code"])

        _result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[only_json_response, retry_response],
            tools_to_use=["create_document", "execute_python_code"],
        )

        second_call_kwargs = mock_client.chat_with_tools.call_args_list[1]
        mensagem_retry = (
            second_call_kwargs.kwargs.get("mensagem")
            or (second_call_kwargs.args[0] if second_call_kwargs.args else None)
        )

        assert "Gere o relatório completo do aluno." in mensagem_retry
        assert "CONTEXTO ORIGINAL DA ETAPA" in mensagem_retry
        assert "student123" in mensagem_retry
        assert "NUNCA use placeholders" in mensagem_retry


# ============================================================
# TEST 3: Only PDF → retry with JSON mention
# ============================================================

class TestOnlyPdfTriggersRetry:
    """When only execute_python_code appears in tool_calls (no create_document),
    a second call to chat_with_tools must happen and the follow-up message
    must mention JSON or documento."""

    async def test_only_pdf_triggers_retry(self):
        """Only execute_python_code called → retry triggered.

        Currently FAILS: chat_with_tools is called once and returns immediately.
        """
        only_pdf_response = _tool_response(["execute_python_code"])
        retry_response = _tool_response(["create_document", "execute_python_code"])

        result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[only_pdf_response, retry_response],
            tools_to_use=["create_document", "execute_python_code"],
        )

        call_count = mock_client.chat_with_tools.call_count
        assert call_count == 2, (
            f"Only execute_python_code in first response → retry expected. "
            f"chat_with_tools should be called TWICE. Got call_count={call_count}."
        )

    async def test_only_pdf_retry_message_mentions_document(self):
        """The retry follow-up message must reference JSON/documento.

        Currently FAILS: no second call exists.
        """
        only_pdf_response = _tool_response(["execute_python_code"])
        retry_response = _tool_response(["create_document", "execute_python_code"])

        _result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[only_pdf_response, retry_response],
            tools_to_use=["create_document", "execute_python_code"],
        )

        call_count = mock_client.chat_with_tools.call_count
        assert call_count == 2, (
            f"Retry call expected but got call_count={call_count}."
        )

        second_call_kwargs = mock_client.chat_with_tools.call_args_list[1]
        mensagem_retry = (
            second_call_kwargs.kwargs.get("mensagem")
            or (second_call_kwargs.args[0] if second_call_kwargs.args else None)
        )

        assert mensagem_retry is not None, (
            "Second (retry) call must receive a mensagem argument."
        )

        mensagem_lower = mensagem_retry.lower()
        has_doc_ref = any(
            keyword in mensagem_lower
            for keyword in ["json", "documento", "document", "create_document"]
        )
        assert has_doc_ref, (
            f"Retry message must mention JSON/documento so the model knows what to create. "
            f"Got mensagem_retry={mensagem_retry!r}"
        )


# ============================================================
# TEST 4: Retry succeeds — both outputs on second call
# ============================================================

class TestRetrySucceedsBothOutputs:
    """First call: only create_document. Retry: both outputs produced.
    Result must be sucesso=True and tentativas=2."""

    async def test_retry_succeeds_both_outputs_produced(self):
        """First call → only JSON. Retry → both JSON + PDF. sucesso=True, tentativas=2.

        Currently FAILS on both:
        - call_count will be 1 (no retry logic exists yet)
        - tentativas will be 1 (retry never happened)
        """
        first_response = _tool_response(["create_document"])
        retry_response = _tool_response(["create_document", "execute_python_code"])

        result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[first_response, retry_response],
            tools_to_use=["create_document", "execute_python_code"],
        )

        assert isinstance(result, ResultadoExecucao)
        assert result.sucesso is True, (
            f"Retry succeeded (both outputs on second call) → sucesso must be True. "
            f"Got sucesso={result.sucesso}."
        )

        assert result.tentativas == 2, (
            f"First call + one retry = 2 attempts total. "
            f"Got tentativas={result.tentativas}. "
            "Current code always returns tentativas=1 because retry logic is missing."
        )

    async def test_retry_succeeds_call_count_is_two(self):
        """Confirm exactly two calls: original + one retry (not three)."""
        first_response = _tool_response(["create_document"])
        retry_response = _tool_response(["create_document", "execute_python_code"])

        _result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[first_response, retry_response],
            tools_to_use=["create_document", "execute_python_code"],
        )

        call_count = mock_client.chat_with_tools.call_count
        assert call_count == 2, (
            f"Expected exactly 2 calls (original + one retry). Got call_count={call_count}."
        )


# ============================================================
# TEST 5: Both retries fail partial → saved with warning
# ============================================================

class TestRetryFailsPartialSavedWithWarning:
    """Both calls produce only create_document (no execute_python_code).
    P0 behavior: fail high instead of saving partial output as success."""

    async def test_retry_fails_partial_saved_with_warning(self):
        """Both calls: only create_document. sucesso=False and a warning alert is added."""
        only_json_first = _tool_response(["create_document"])
        only_json_retry = _tool_response(["create_document"])

        result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[only_json_first, only_json_retry],
            tools_to_use=["create_document", "execute_python_code"],
        )

        assert isinstance(result, ResultadoExecucao)

        assert result.sucesso is False, (
            f"Partial output must fail high after retry fails. "
            f"Got sucesso={result.sucesso}."
        )
        assert "Saída obrigatória incompleta" in (result.erro or "")

        warning_alerts = [
            a for a in result.alertas
            if a.get("tipo") == "aviso" or a.get("tipo") == "warning"
        ]
        assert len(warning_alerts) >= 1, (
            f"After two failed dual-output attempts, a warning alert must be added to alertas. "
            f"Got alertas={result.alertas}. "
            "Current code adds only an 'info' alert (no warning) and never retries."
        )

    async def test_retry_fails_partial_call_count_is_two(self):
        """Even when retry fails, exactly two calls should have been made."""
        only_json_first = _tool_response(["create_document"])
        only_json_retry = _tool_response(["create_document"])

        _result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[only_json_first, only_json_retry],
            tools_to_use=["create_document", "execute_python_code"],
        )

        call_count = mock_client.chat_with_tools.call_count
        assert call_count == 2, (
            f"Retry was attempted (even though it failed) → call_count must be 2. "
            f"Got call_count={call_count}."
        )

    async def test_retry_fails_warning_message_mentions_partial(self):
        """Warning alert message must communicate that output is incomplete/partial."""
        only_json_first = _tool_response(["create_document"])
        only_json_retry = _tool_response(["create_document"])

        result, _mock_client = await _call_executar_com_tools(
            chat_side_effect=[only_json_first, only_json_retry],
            tools_to_use=["create_document", "execute_python_code"],
        )

        warning_alerts = [
            a for a in result.alertas
            if a.get("tipo") in ("aviso", "warning")
        ]
        assert len(warning_alerts) >= 1, (
            f"No warning alert found. Got alertas={result.alertas}"
        )

        warning_mensagem = warning_alerts[0].get("mensagem", "")
        mensagem_lower = warning_mensagem.lower()
        has_partial_ref = any(
            keyword in mensagem_lower
            for keyword in [
                "incompleto", "incompleta", "falhar", "falha",
                "pdf", "execute_python_code", "faltando", "ausente", "fallback",
            ]
        )
        assert has_partial_ref, (
            f"Warning message should communicate that output is partial/incomplete. "
            f"Got warning mensagem={warning_mensagem!r}"
        )


# ============================================================
# TEST 6: Single tool in tools_to_use → no dual-output check
# ============================================================

class TestSingleToolNoDualCheck:
    """When tools_to_use contains only one tool (e.g., ["create_document"]),
    the dual-output check must NOT apply — no retry even if execute_python_code
    is absent from tool_calls."""

    async def test_single_tool_in_tools_to_use_no_dual_check(self):
        """tools_to_use=["create_document"] only → dual check does NOT apply.

        Only one type of output is expected, so producing only create_document
        is a complete (not partial) result. No retry should happen.

        This test verifies that the dual-output guard is gated on whether BOTH
        tool types are in tools_to_use — not just on what the model returns.
        """
        only_json_response = _tool_response(["create_document"])

        result, mock_client = await _call_executar_com_tools(
            chat_side_effect=only_json_response,
            tools_to_use=["create_document"],  # Only one tool — no dual check
        )

        assert isinstance(result, ResultadoExecucao)
        assert result.sucesso is True, (
            f"Single tool in tools_to_use → no dual-output check → sucesso=True. "
            f"Got sucesso={result.sucesso}."
        )

        call_count = mock_client.chat_with_tools.call_count
        assert call_count == 1, (
            f"tools_to_use=['create_document'] only → no retry should happen. "
            f"chat_with_tools must be called exactly once. Got call_count={call_count}."
        )

    async def test_single_tool_execute_python_only_no_dual_check(self):
        """tools_to_use=["execute_python_code"] only → dual check does NOT apply.

        Producing only execute_python_code is a complete result for this call.
        """
        only_pdf_response = _tool_response(["execute_python_code"])

        result, mock_client = await _call_executar_com_tools(
            chat_side_effect=only_pdf_response,
            tools_to_use=["execute_python_code"],
        )

        assert result.sucesso is True, (
            f"Single tool (execute_python_code only) → sucesso=True. "
            f"Got sucesso={result.sucesso}."
        )

        call_count = mock_client.chat_with_tools.call_count
        assert call_count == 1, (
            f"tools_to_use=['execute_python_code'] only → no retry. "
            f"Got call_count={call_count}."
        )

    async def test_empty_tools_to_use_no_dual_check(self):
        """tools_to_use=None (default) with only one output type.

        When tools_to_use is None, the function expands to the default list which
        includes both tools → dual-output check DOES apply. This is the opposite
        of the single-tool case. We confirm that with default tools, partial output
        triggers a retry (call_count > 1).

        Currently FAILS: no retry exists, so call_count will be 1.
        """
        only_json_response = _tool_response(["create_document"])
        retry_response = _tool_response(["create_document", "execute_python_code"])

        _result, mock_client = await _call_executar_com_tools(
            chat_side_effect=[only_json_response, retry_response],
            tools_to_use=None,  # Expands to default: both tools → dual check applies
        )

        call_count = mock_client.chat_with_tools.call_count
        assert call_count == 2, (
            f"tools_to_use=None expands to both tools → dual-output check applies → "
            f"retry expected on partial output. Got call_count={call_count}. "
            "Current code never retries — this is the bug E-T2 must fix."
        )


@pytest.mark.asyncio
async def test_pdf_execution_error_triggers_same_model_code_repair(monkeypatch, tmp_path):
    """A failed execute_python_code PDF attempt gets one explicit same-model repair."""
    import chat_service
    import fitz
    from chat_service import ProviderType

    feedback = "A aluna demonstrou bom dominio geral, mas precisa revisar porcentagem."
    json_path = tmp_path / "correcao.json"
    json_path.write_text(
        json.dumps(
            {
                "nota_final": 8,
                "questoes": [
                    {
                        "numero": 1,
                        "resposta_aluno": "x = 5",
                        "resposta_correta": "x = 5",
                        "nota": 8,
                        "nota_maxima": 8,
                        "acerto": True,
                        "feedback": "Bom desempenho.",
                    }
                ],
                "total_acertos": 1,
                "total_erros": 0,
                "feedback_geral": feedback,
                "_avisos_documento": [],
                "_avisos_questao": [],
            }
        ),
        encoding="utf-8",
    )
    pdf_path = tmp_path / "correcao.pdf"
    pdf = fitz.open()
    page = pdf.new_page()
    page.insert_textbox(
        fitz.Rect(40, 40, 560, 800),
        "Aluno: Ada\n"
        "Matéria: Matemática\n"
        "Atividade: Prova 1\n"
        "Data: 2026-05-17\n"
        "Nota final: 8.0\n"
        "Questão 1 — Nota: 8.0\n"
        f"Feedback Geral: {feedback}\n",
        fontsize=11,
    )
    pdf.save(str(pdf_path))
    pdf.close()

    docs = {
        "doc-json": SimpleNamespace(
            id="doc-json",
            extensao=".json",
            metadata={"tool": "create_document"},
            status=StatusProcessamento.CONCLUIDO,
        ),
        "doc-pdf": SimpleNamespace(
            id="doc-pdf",
            extensao=".pdf",
            metadata={"tool": "execute_python_code"},
            status=StatusProcessamento.CONCLUIDO,
        ),
    }
    paths = {"doc-json": json_path, "doc-pdf": pdf_path}

    class FakeStorage:
        atualizar_documento_processamento = MagicMock()

        def get_documento(self, doc_id):
            return docs.get(doc_id)

        def resolver_caminho_documento(self, doc):
            return paths[doc.id]

    model = SimpleNamespace(
        id="gemini-lite",
        tipo=ProviderType.GOOGLE,
        modelo="gemini-2.5-flash-lite",
        api_key_id=None,
        suporta_function_calling=True,
        max_tokens=1024,
        temperature=0,
        suporta_temperature=False,
    )
    monkeypatch.setattr(chat_service.model_manager, "get", lambda _model_id: model)
    monkeypatch.setattr(chat_service.api_key_manager, "get", lambda _key_id: None)
    monkeypatch.setattr(
        chat_service.api_key_manager,
        "get_por_empresa",
        lambda _provider: SimpleNamespace(api_key="test-key"),
    )

    calls = []

    class DummyClient:
        def __init__(self, model_config, api_key):
            pass

        async def chat_with_tools(self, **kwargs):
            calls.append(kwargs)
            context = kwargs["context"]
            if len(calls) == 1:
                context.created_document_ids.append("doc-json")
                return _tool_response(["create_document"])
            if len(calls) == 2:
                return {
                    "content": "",
                    "tokens": 20,
                    "input_tokens": 15,
                    "output_tokens": 5,
                    "modelo": "gemini-2.5-flash-lite",
                    "provider": "google",
                    "tool_calls": [
                        {
                            "name": "execute_python_code",
                            "is_error": True,
                            "error_content": "[E2B_ERROR] IndentationError: unexpected indent",
                        }
                    ],
                }
            context.created_document_ids.append("doc-pdf")
            return _tool_response(["execute_python_code"])

    monkeypatch.setattr(chat_service, "ChatClient", DummyClient)

    executor = PipelineExecutor()
    executor.storage = FakeStorage()
    result = await executor.executar_com_tools(
        mensagem="Gere analise de habilidades.",
        atividade_id="atividade-1",
        aluno_id="aluno-1",
        provider_id="gemini-lite",
        tools_to_use=["create_document", "execute_python_code"],
        expected_document_type=TipoDocumento.CORRECAO,
    )

    assert result.sucesso is True
    assert result.tentativas == 3
    assert len(calls) == 3
    assert calls[2]["tools"][0]["name"] == "execute_python_code"
    assert "tentativa anterior" in calls[2]["mensagem"].lower()
    assert "IndentationError" in calls[2]["mensagem"]
    assert "Nao chame create_document" in calls[2]["mensagem"]


@pytest.mark.asyncio
async def test_pdf_json_consistency_gets_two_same_model_repairs(monkeypatch, tmp_path):
    """PDF/JSON inconsistency may get two explicit same-model PDF repairs."""
    import chat_service
    import fitz
    from chat_service import ProviderType

    feedback = (
        "Ótima atuação na maior parte da prova. Pontos fortes: resolução de "
        "equações lineares, aplicação correta da ordem de operações e uso "
        "adequado da fórmula da área. Ponto a melhorar: revisar porcentagens "
        "e manter a unidade de medida consistente."
    )
    json_path = tmp_path / "correcao.json"
    json_path.write_text(
        json.dumps(
            {
                "nota_final": 8,
                "questoes": [
                    {
                        "numero": 1,
                        "resposta_aluno": "x = 5",
                        "resposta_correta": "x = 5",
                        "nota": 8,
                        "nota_maxima": 8,
                        "acerto": True,
                        "feedback": "Bom desempenho.",
                    }
                ],
                "total_acertos": 1,
                "total_erros": 0,
                "feedback_geral": feedback,
                "_avisos_documento": [],
                "_avisos_questao": [],
            }
        ),
        encoding="utf-8",
    )

    def write_pdf(path, feedback_text):
        pdf = fitz.open()
        page = pdf.new_page()
        page.insert_textbox(
            fitz.Rect(40, 40, 560, 800),
            "Aluno: Ada\n"
            "Matéria: Matemática\n"
            "Atividade: Prova 1\n"
            "Data: 2026-05-17\n"
            "Nota final: 8.0\n"
            "Questão 1 — Nota: 8.0\n"
            f"Feedback Geral: {feedback_text}\n",
            fontsize=11,
        )
        pdf.save(str(path))
        pdf.close()

    bad_pdf_1 = tmp_path / "correcao_bad_1.pdf"
    bad_pdf_2 = tmp_path / "correcao_bad_2.pdf"
    good_pdf = tmp_path / "correcao_good.pdf"
    write_pdf(bad_pdf_1, "Ótima atuação")
    write_pdf(bad_pdf_2, "Ótima atuação na maior parte da prova")
    write_pdf(good_pdf, feedback)

    docs = {
        "doc-json": SimpleNamespace(
            id="doc-json",
            extensao=".json",
            metadata={"tool": "create_document"},
            status=StatusProcessamento.CONCLUIDO,
        ),
        "doc-pdf-bad-1": SimpleNamespace(
            id="doc-pdf-bad-1",
            extensao=".pdf",
            metadata={"tool": "execute_python_code"},
            status=StatusProcessamento.CONCLUIDO,
        ),
        "doc-pdf-bad-2": SimpleNamespace(
            id="doc-pdf-bad-2",
            extensao=".pdf",
            metadata={"tool": "execute_python_code"},
            status=StatusProcessamento.CONCLUIDO,
        ),
        "doc-pdf-good": SimpleNamespace(
            id="doc-pdf-good",
            extensao=".pdf",
            metadata={"tool": "execute_python_code"},
            status=StatusProcessamento.CONCLUIDO,
        ),
    }
    paths = {
        "doc-json": json_path,
        "doc-pdf-bad-1": bad_pdf_1,
        "doc-pdf-bad-2": bad_pdf_2,
        "doc-pdf-good": good_pdf,
    }

    class FakeStorage:
        atualizar_documento_processamento = MagicMock()

        def get_documento(self, doc_id):
            return docs.get(doc_id)

        def resolver_caminho_documento(self, doc):
            return paths[doc.id]

    model = SimpleNamespace(
        id="gemini-lite",
        tipo=ProviderType.GOOGLE,
        modelo="gemini-2.5-flash-lite",
        api_key_id=None,
        suporta_function_calling=True,
        max_tokens=1024,
        temperature=0,
        suporta_temperature=False,
    )
    monkeypatch.setattr(chat_service.model_manager, "get", lambda _model_id: model)
    monkeypatch.setattr(chat_service.api_key_manager, "get", lambda _key_id: None)
    monkeypatch.setattr(
        chat_service.api_key_manager,
        "get_por_empresa",
        lambda _provider: SimpleNamespace(api_key="test-key"),
    )

    calls = []

    class DummyClient:
        def __init__(self, model_config, api_key):
            pass

        async def chat_with_tools(self, **kwargs):
            calls.append(kwargs)
            context = kwargs["context"]
            if len(calls) == 1:
                context.created_document_ids.append("doc-json")
                return _tool_response(["create_document"])
            if len(calls) == 2:
                context.created_document_ids.append("doc-pdf-bad-1")
                return _tool_response(["execute_python_code"])
            if len(calls) == 3:
                context.created_document_ids.append("doc-pdf-bad-2")
                return _tool_response(["execute_python_code"])
            context.created_document_ids.append("doc-pdf-good")
            return _tool_response(["execute_python_code"])

    monkeypatch.setattr(chat_service, "ChatClient", DummyClient)

    executor = PipelineExecutor()
    executor.storage = FakeStorage()
    result = await executor.executar_com_tools(
        mensagem="Gere correção.",
        atividade_id="atividade-1",
        aluno_id="aluno-1",
        provider_id="gemini-lite",
        tools_to_use=["create_document", "execute_python_code"],
        expected_document_type=TipoDocumento.CORRECAO,
    )

    assert result.sucesso is True
    assert result.tentativas == 4
    assert len(calls) == 4
    mensagens = [alerta["mensagem"] for alerta in result.alertas]
    assert any("retry 1/2" in mensagem for mensagem in mensagens)
    assert any("retry 2/2" in mensagem for mensagem in mensagens)
    assert "Feedback Geral" in calls[2]["mensagem"]
    assert "feedback_geral" in calls[2]["mensagem"]
    assert "Feedback Geral" in calls[3]["mensagem"]


@pytest.mark.asyncio
async def test_codigo_composto_de_aviso_falha_alto_no_tool_runtime():
    """Runtime tool output with A|B|C warning code must not be accepted."""
    invalid_report = {
        "resumo_geral": "Aluno com bom desempenho.",
        "pontos_fortes": ["Organização"],
        "areas_melhoria": ["Justificativas"],
        "recomendacoes": [
            {"tipo": "pratica", "descricao": "Refazer questões", "prioridade": "media"}
        ],
        "nota_final": 8.0,
        "detalhamento": "Detalhes por questão.",
        "_avisos_documento": [],
        "_avisos_questao": [
            {
                "codigo": "ILLEGIBLE_QUESTION|MISSING_CONTENT|LOW_CONFIDENCE",
                "questao": 2,
                "explicacao": "Código composto vindo do modelo",
            }
        ],
        "_fontes_utilizadas": ["CORRIGIR", "ANALISAR_HABILIDADES"],
    }
    repaired_report = {
        **invalid_report,
        "_avisos_questao": [
            {
                "codigo": "LOW_CONFIDENCE",
                "questao": 2,
                "explicacao": "Leitura com baixa confiança",
            }
        ],
    }

    result, mock_client = await _call_executar_com_tools(
        chat_side_effect=[
            _tool_response_with_json_content(invalid_report),
            _tool_response_with_json_content(repaired_report),
        ],
        tools_to_use=["create_document", "execute_python_code"],
        expected_document_type=TipoDocumento.RELATORIO_FINAL,
    )

    assert result.sucesso is False
    assert result.tentativas == 2
    assert mock_client.chat_with_tools.call_count == 2
    assert "codigo composto" in result.erro
