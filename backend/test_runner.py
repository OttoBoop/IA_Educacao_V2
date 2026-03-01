#!/usr/bin/env python3
"""
NOVO CR - Executor de Testes Unificado

CLI para execução de testes do pipeline de correção.

Uso:
    # Gerar dados de teste (primeira vez)
    python test_runner.py --generate-data --mini

    # Executar todos os testes locais (usa modelos baratos por padrão)
    python test_runner.py --local

    # Usar modelos mais caros/potentes
    python test_runner.py --local --full

    # Por provider
    python test_runner.py --local --provider openai
    python test_runner.py --local --provider anthropic
    python test_runner.py --local --provider google

    # Por modelo específico
    python test_runner.py --local --model gpt-4o-mini

    # Apenas modelos reasoning
    python test_runner.py --local --reasoning

    # Para ambiente Render
    python test_runner.py --render --skip-expensive

    # Cenários específicos
    python test_runner.py --scenario happy-path
    python test_runner.py --scenario corrupted-docs

    # Gerar relatório
    python test_runner.py --local --report html

Modelos por modo:
    --cheap (padrão): Modelos novos e econômicos
        OpenAI: gpt-5-mini ($0.25/$2.00)
        Anthropic: claude-haiku-4-5-20251001 ($1.00/$5.00)
        Google: gemini-3-flash-preview ($0.30/$1.20)

    --full: Modelos potentes
        OpenAI: gpt-5 ($1.25/$10.00)
        Anthropic: claude-sonnet-4-5-20250929 ($3.00/$15.00)
        Google: gemini-3-pro-preview ($2.00/$15.00)

    --legacy: Modelos antigos (mais baratos)
        OpenAI: gpt-4o-mini ($0.15/$0.60)
        Anthropic: claude-3-5-haiku-20241022 ($0.80/$4.00)
        Google: gemini-2.5-flash ($0.10/$0.40)

NOTE: Gemini 3 models require "-preview" suffix. Gemini 2.0 deprecated (EOL March 2026).
Model IDs verified working as of January 2026.
"""

import argparse
import sys
import os
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


# Diretório base
BASE_DIR = Path(__file__).parent
TESTS_DIR = BASE_DIR / "tests"
REPORTS_DIR = BASE_DIR / "test_reports"
LOGS_DIR = BASE_DIR / "logs"

# Configuração de modelos por modo
# Model IDs verified working as of January 2026
# NOTE: Gemini 3 requires "-preview" suffix (gemini-3-pro-preview, gemini-3-flash-preview)
# NOTE: Gemini 2.0 deprecated, shutting down March 31, 2026 - use 2.5 for legacy
MODEL_CONFIGS = {
    "cheap": {
        "openai": "gpt-5-mini",           # $0.25/$2.00 - novo e barato
        "anthropic": "claude-haiku-4-5-20251001",  # $1.00/$5.00 - Haiku 4.5
        "google": "gemini-3-flash-preview",  # $0.30/$1.20 - Gemini 3 (requires -preview suffix)
        "description": "Modelos novos e econômicos (recomendado para testes)"
    },
    "full": {
        "openai": "gpt-5",                # $1.25/$10.00
        "anthropic": "claude-sonnet-4-5-20250929",  # $3.00/$15.00
        "google": "gemini-3-pro-preview",    # $2.00/$15.00 - Gemini 3 (requires -preview suffix)
        "description": "Modelos potentes (maior custo)"
    },
    "reasoning": {
        "openai": "o3-mini",              # $1.10/$4.40 - reasoning
        "anthropic": "claude-sonnet-4-5-20250929",  # Com extended thinking
        "google": "gemini-3-pro-preview",    # Com thinking nativo (requires -preview suffix)
        "description": "Modelos com reasoning/thinking"
    },
    "legacy": {
        "openai": "gpt-4o-mini",          # $0.15/$0.60 - legado barato
        "anthropic": "claude-3-5-haiku-20241022",  # $0.80/$4.00 - legado
        "google": "gemini-2.5-flash",     # $0.10/$0.40 - stable (2.0 deprecated EOL Mar 2026)
        "description": "Modelos legados (mais baratos, menos capazes)"
    }
}


def ensure_dirs():
    """Garante que diretórios necessários existem"""
    REPORTS_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)


def generate_test_data(mini: bool = False, completo: bool = False, limpar: bool = False):
    """Gera dados de teste usando test_data_generator.py"""
    print("\n" + "=" * 60)
    print("GERANDO DADOS DE TESTE")
    print("=" * 60)

    cmd = [sys.executable, str(BASE_DIR / "test_data_generator.py")]

    if limpar:
        cmd.append("--limpar")
    if mini:
        cmd.append("--mini")
    elif completo:
        cmd.append("--completo")

    result = subprocess.run(cmd, cwd=str(BASE_DIR))
    return result.returncode == 0


def get_model_for_provider(provider: str, mode: str) -> str:
    """Retorna o modelo apropriado para o provider baseado no modo."""
    config = MODEL_CONFIGS.get(mode, MODEL_CONFIGS["cheap"])
    return config.get(provider, config["openai"])


def build_pytest_args(args) -> List[str]:
    """Constrói argumentos para pytest"""
    pytest_args = [str(TESTS_DIR)]

    # Verbosidade
    pytest_args.append("-v")  # Sempre verbose por padrão
    if args.verbose:
        pytest_args.extend(["-s", "--tb=long"])  # Mostrar prints e tracebacks completos

    # Determinar modo de modelo
    if args.full:
        model_mode = "full"
    elif getattr(args, 'legacy', False):
        model_mode = "legacy"
    elif args.reasoning:
        model_mode = "reasoning"
    else:
        model_mode = "cheap"

    # Provider/Model
    if args.model:
        # Modelo específico tem prioridade
        pytest_args.extend(["--model", args.model])
    elif args.provider:
        # Se provider especificado, usar modelo do modo atual
        model = get_model_for_provider(args.provider, model_mode)
        pytest_args.extend(["--model", model])
        pytest_args.extend(["--provider", args.provider])
    else:
        # Passar o modo para conftest usar
        pytest_args.extend(["--model-mode", model_mode])

    if args.provider and args.model:
        pytest_args.extend(["--provider", args.provider])

    # Skip expensive
    if args.skip_expensive:
        pytest_args.append("--skip-expensive")

    # Timeout
    if args.timeout:
        pytest_args.extend(["--timeout", str(args.timeout)])

    # Reasoning only
    if args.reasoning:
        pytest_args.extend(["-m", "reasoning"])

    # Cenário específico
    if args.scenario:
        scenario_map = {
            "happy-path": "tests/scenarios/test_happy_path.py",
            "corrupted-docs": "tests/scenarios/test_corrupted_docs.py",
            "skip-steps": "tests/scenarios/test_skip_steps.py"
        }
        if args.scenario in scenario_map:
            pytest_args = [scenario_map[args.scenario]] + pytest_args[1:]
        else:
            # Tentar como marcador
            pytest_args.extend(["-m", args.scenario.replace("-", "_")])

    # Marcadores por provider
    if args.provider and not args.model:
        pytest_args.extend(["-m", args.provider])

    # Relatório
    if args.report == "html":
        pytest_args.extend([
            f"--html={REPORTS_DIR / 'report.html'}",
            "--self-contained-html"
        ])
    elif args.report == "json":
        pytest_args.extend([
            f"--json-report",
            f"--json-report-file={REPORTS_DIR / 'results.json'}"
        ])

    # Cobertura
    if args.coverage:
        pytest_args.extend([
            "--cov=.",
            f"--cov-report=html:{REPORTS_DIR / 'coverage'}"
        ])

    return pytest_args


def run_pytest(args) -> int:
    """Executa pytest com os argumentos configurados"""
    ensure_dirs()

    pytest_args = build_pytest_args(args)

    print("\n" + "=" * 60)
    print("EXECUTANDO TESTES")
    print("=" * 60)
    print(f"Comando: pytest {' '.join(pytest_args)}")
    print("=" * 60 + "\n")

    # Configurar ambiente
    env = os.environ.copy()
    if args.render:
        env["RENDER"] = "true"

    # CRITICAL: Add backend to PYTHONPATH so imports work
    env["PYTHONPATH"] = str(BASE_DIR)
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))

    # Executar pytest
    try:
        import pytest
        return pytest.main(pytest_args)
    except ImportError:
        # Fallback para subprocess
        cmd = [sys.executable, "-m", "pytest"] + pytest_args
        result = subprocess.run(cmd, cwd=str(BASE_DIR), env=env)
        return result.returncode


def check_api_keys():
    """Verifica quais API keys estão disponíveis"""
    print("\n" + "=" * 60)
    print("VERIFICANDO API KEYS")
    print("=" * 60)

    keys = {
        "OPENAI_API_KEY": "OpenAI (GPT)",
        "ANTHROPIC_API_KEY": "Anthropic (Claude)",
        "GOOGLE_API_KEY": "Google (Gemini)",
        "DEEPSEEK_API_KEY": "DeepSeek",
        "MISTRAL_API_KEY": "Mistral"
    }

    available = []
    missing = []

    for key, name in keys.items():
        if os.getenv(key):
            available.append(name)
            print(f"  [OK] {name}")
        else:
            missing.append(name)
            print(f"  [--] {name} (não configurada)")

    print()
    return available, missing


def analyze_failures(pytest_output: str, command: str) -> Optional[Path]:
    """
    Analisa falhas de teste e gera relatório detalhado.

    Args:
        pytest_output: Saída do pytest
        command: Comando executado

    Returns:
        Path do relatório gerado ou None se não houver falhas
    """
    try:
        from tests.utils.log_parser import TestResultParser, ReportGenerator

        parser = TestResultParser()
        result = parser.parse_pytest_output(pytest_output)

        if result.failed == 0 and result.errors == 0:
            print("\n[OK] Sem falhas para analisar")
            return None

        # Gerar relatório
        generator = ReportGenerator()
        report_content = generator.generate_markdown(result, command)

        # Salvar relatório
        report_path = REPORTS_DIR / "analysis_report.md"
        report_path.write_text(report_content, encoding="utf-8")

        print(f"\n[REPORT] Relatorio de analise gerado: {report_path}")
        print(f"   - Testes: {result.total} total, {result.passed} passed, {result.failed} failed")
        print(f"   - Taxa de sucesso: {result.success_rate:.1f}%")

        if result.failures:
            print("\n[SUMMARY] Resumo de falhas:")
            # Agrupar por categoria
            by_category = {}
            for f in result.failures:
                cat = f.category.value
                if cat not in by_category:
                    by_category[cat] = []
                by_category[cat].append(f)

            for cat, failures in by_category.items():
                print(f"   - {cat.replace('_', ' ').title()}: {len(failures)}")

        # Também salvar JSON para análise programática
        json_report = generator.generate_json(result)
        json_path = REPORTS_DIR / "analysis_report.json"
        with open(json_path, "w", encoding="utf-8") as f:
            import json as json_module
            json_module.dump(json_report, f, indent=2)

        return report_path

    except ImportError as e:
        print(f"\n[WARN] Nao foi possivel importar modulo de analise: {e}")
        print("   Execute: pip install -e .")
        return None
    except Exception as e:
        print(f"\n[WARN] Erro ao analisar falhas: {e}")
        return None


def print_summary(args):
    """Imprime resumo da configuração"""
    print("\n" + "=" * 60)
    print("CONFIGURAÇÃO DE TESTES")
    print("=" * 60)

    print(f"  Ambiente: {'Render' if args.render else 'Local'}")

    # Determinar modo de modelo
    if args.full:
        model_mode = "full"
    elif getattr(args, 'legacy', False):
        model_mode = "legacy"
    elif args.reasoning:
        model_mode = "reasoning"
    else:
        model_mode = "cheap"

    mode_config = MODEL_CONFIGS[model_mode]
    print(f"  Modo: {model_mode} - {mode_config['description']}")

    if args.provider:
        model = get_model_for_provider(args.provider, model_mode)
        print(f"  Provider: {args.provider} → {model}")
    elif args.model:
        print(f"  Modelo: {args.model}")
    else:
        print(f"  Modelos padrão:")
        print(f"    OpenAI: {mode_config['openai']}")
        print(f"    Anthropic: {mode_config['anthropic']}")
        print(f"    Google: {mode_config['google']}")

    if args.reasoning:
        print(f"  Tipo: Apenas reasoning")
    if args.skip_expensive:
        print(f"  Modelos caros: Pulados")
    if args.scenario:
        print(f"  Cenário: {args.scenario}")
    if args.timeout:
        print(f"  Timeout: {args.timeout}s")
    if args.report:
        print(f"  Relatório: {args.report}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="NOVO CR - Executor de Testes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python test_runner.py --generate-data --mini
  python test_runner.py --local
  python test_runner.py --local --provider openai
  python test_runner.py --local --model gpt-4o-mini
  python test_runner.py --render --skip-expensive
  python test_runner.py --scenario happy-path
        """
    )

    # Modo de execução
    mode = parser.add_argument_group("Modo de Execução")
    mode.add_argument("--local", action="store_true",
                      help="Executar testes locais")
    mode.add_argument("--render", action="store_true",
                      help="Executar testes para ambiente Render")

    # Seleção de modelos
    models = parser.add_argument_group("Seleção de Modelos")
    model_mode = models.add_mutually_exclusive_group()
    model_mode.add_argument("--cheap", action="store_true", default=True,
                            help="Usar modelos novos e baratos (padrão): gpt-5-mini, claude-haiku-4-5, gemini-3-flash-preview")
    model_mode.add_argument("--full", action="store_true",
                            help="Usar modelos potentes: gpt-5, claude-sonnet-4-5, gemini-3-pro-preview")
    model_mode.add_argument("--legacy", action="store_true",
                            help="Usar modelos legados (mais baratos): gpt-4o-mini, claude-3-5-haiku, gemini-2.5-flash")

    # Filtros
    filters = parser.add_argument_group("Filtros")
    filters.add_argument("--provider",
                         choices=["openai", "anthropic", "google", "deepseek", "mistral"],
                         help="Provider específico")
    filters.add_argument("--model",
                         help="Modelo específico (ex: gpt-4o-mini)")
    filters.add_argument("--reasoning", action="store_true",
                         help="Apenas modelos reasoning")
    filters.add_argument("--scenario",
                         choices=["happy-path", "corrupted-docs", "skip-steps"],
                         help="Cenário específico")

    # Geração de dados
    data = parser.add_argument_group("Geração de Dados")
    data.add_argument("--generate-data", action="store_true",
                      help="Gerar dados de teste")
    data.add_argument("--mini", action="store_true",
                      help="Dados mínimos (2 alunos)")
    data.add_argument("--completo", action="store_true",
                      help="Dados completos (50 alunos)")
    data.add_argument("--limpar", action="store_true",
                      help="Limpar dados antes de gerar")

    # Opções
    options = parser.add_argument_group("Opções")
    options.add_argument("--skip-expensive", action="store_true",
                         help="Pular modelos caros")
    options.add_argument("--timeout", type=int, default=120,
                         help="Timeout em segundos (default: 120)")
    options.add_argument("-v", "--verbose", action="store_true",
                         help="Saída detalhada")
    options.add_argument("--coverage", action="store_true",
                         help="Gerar cobertura de código")

    # Relatórios
    reports = parser.add_argument_group("Relatórios")
    reports.add_argument("--report",
                         choices=["html", "json", "console"],
                         default="console",
                         help="Formato do relatório")

    # Utilitários
    utils = parser.add_argument_group("Utilitários")
    utils.add_argument("--check-keys", action="store_true",
                       help="Verificar API keys disponíveis")
    utils.add_argument("--list-tests", action="store_true",
                       help="Listar testes disponíveis")

    # Análise de falhas
    analysis = parser.add_argument_group("Análise de Falhas")
    analysis.add_argument("--analyze-failures", action="store_true",
                          help="Analisar falhas e gerar relatório detalhado")
    analysis.add_argument("--with-rollback", action="store_true",
                          help="Salvar estado antes de auto-fix (requer --analyze-failures)")

    args = parser.parse_args()

    # Verificar API keys
    if args.check_keys:
        check_api_keys()
        return 0

    # Listar testes
    if args.list_tests:
        print("\n" + "=" * 60)
        print("TESTES DISPONÍVEIS")
        print("=" * 60)

        for test_file in sorted(TESTS_DIR.rglob("test_*.py")):
            rel_path = test_file.relative_to(BASE_DIR)
            print(f"  {rel_path}")

        return 0

    # Gerar dados
    if args.generate_data:
        success = generate_test_data(
            mini=args.mini,
            completo=args.completo,
            limpar=args.limpar
        )
        if not success:
            print("\n[ERRO] Falha ao gerar dados de teste")
            return 1
        if not (args.local or args.render):
            return 0

    # Executar testes
    if args.local or args.render:
        # Se Render, ajustar configurações
        if args.render:
            args.skip_expensive = True
            args.timeout = max(args.timeout, 180)

        # Verificar keys
        available, missing = check_api_keys()

        # Imprimir configuração
        print_summary(args)

        # Se análise de falhas, capturar saída
        if args.analyze_failures:
            import io
            import sys as sys_module
            from contextlib import redirect_stdout, redirect_stderr

            # Capturar saída
            output_buffer = io.StringIO()

            # Construir comando para exibição
            pytest_args = build_pytest_args(args)
            command = f"pytest {' '.join(pytest_args)}"

            # Executar pytest com captura
            print("\n" + "=" * 60)
            print("EXECUTANDO TESTES (com análise de falhas)")
            print("=" * 60)
            print(f"Comando: {command}")
            print("=" * 60 + "\n")

            # Usar subprocess para capturar saída completa
            import subprocess
            env = os.environ.copy()
            env["PYTHONPATH"] = str(BASE_DIR)

            cmd = [sys_module.executable, "-m", "pytest"] + pytest_args
            result = subprocess.run(
                cmd,
                cwd=str(BASE_DIR),
                env=env,
                capture_output=True,
                text=True
            )

            # Mostrar saída
            print(result.stdout)
            if result.stderr:
                print(result.stderr)

            # Analisar falhas
            full_output = result.stdout + "\n" + result.stderr
            analyze_failures(full_output, command)

            return result.returncode

        # Executar normalmente
        return run_pytest(args)

    # Se nenhuma ação, mostrar ajuda
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
