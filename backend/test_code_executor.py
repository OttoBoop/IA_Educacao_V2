"""
Tests for Code Executor

Execute with: python test_code_executor.py

Tests cover:
1. Security validation (blocking dangerous code)
2. Library detection from code
3. Output file detection from code
4. API endpoints
5. E2B integration (actual code execution)
"""

import asyncio
import sys
import os
import json
import base64

sys.path.insert(0, '.')

from code_executor import (
    SecurityValidator,
    detect_libraries_from_code,
    detect_output_files_from_code,
    code_executor,
    ExecutionStatus,
    CodeExecutorConfig,
)


# ============================================================
# TEST UTILITIES
# ============================================================

def test_passed(name: str):
    print(f"   [OK] {name}")

def test_failed(name: str, reason: str):
    print(f"   [FAIL] {name}: {reason}")
    return False

def section(name: str):
    print(f"\n{'='*50}")
    print(f" {name}")
    print(f"{'='*50}")


# ============================================================
# 1. SECURITY VALIDATOR TESTS
# ============================================================

def test_security_validator():
    section("1. SECURITY VALIDATOR TESTS")

    validator = SecurityValidator()
    all_passed = True

    # Test 1.1: Safe code should pass
    safe_codes = [
        "print('Hello, World!')",
        "import pandas as pd\ndf = pd.DataFrame({'a': [1,2,3]})",
        "import matplotlib.pyplot as plt\nplt.plot([1,2,3])",
        "x = 2 + 2\nprint(x)",
        "for i in range(10):\n    print(i)",
        "def calculate(x):\n    return x * 2",
        "import numpy as np\narr = np.array([1,2,3])",
    ]

    for code in safe_codes:
        is_safe, violations = validator.validate(code)
        if is_safe:
            test_passed(f"Safe code accepted: {code[:40]}...")
        else:
            all_passed = test_failed(f"Safe code rejected", f"{violations}")

    # Test 1.2: Dangerous code should be blocked
    dangerous_codes = [
        ("import os\nos.system('rm -rf /')", "os.system"),
        ("import subprocess\nsubprocess.call(['ls'])", "subprocess"),
        ("eval('print(1)')", "eval"),
        ("exec('x = 1')", "exec"),
        ("__import__('os')", "__import__"),
        ("open('/etc/passwd').read()", "file system access"),
        ("import socket\ns = socket.socket()", "network"),
        ("import requests\nrequests.get('http://evil.com')", "network"),
    ]

    for code, reason in dangerous_codes:
        is_safe, violations = validator.validate(code)
        if not is_safe:
            test_passed(f"Blocked {reason}: {code[:40]}...")
        else:
            all_passed = test_failed(f"Should block {reason}", code[:40])

    # Test 1.3: Edge cases
    edge_cases = [
        # Comment with dangerous word should pass
        ("# os.system is dangerous\nprint('safe')", True, "comment with dangerous word"),
        # String with dangerous content should pass
        ("msg = 'use subprocess for commands'\nprint(msg)", True, "string with dangerous word"),
        # Nested function
        ("def f():\n    def g():\n        return 1\n    return g()", True, "nested functions"),
    ]

    for code, should_pass, description in edge_cases:
        is_safe, violations = validator.validate(code)
        if is_safe == should_pass:
            test_passed(f"Edge case: {description}")
        else:
            all_passed = test_failed(f"Edge case: {description}", f"Expected {should_pass}, got {is_safe}")

    return all_passed


# ============================================================
# 2. LIBRARY DETECTION TESTS
# ============================================================

def test_library_detection():
    section("2. LIBRARY DETECTION TESTS")

    all_passed = True

    test_cases = [
        # (code, expected_libraries)
        (
            "import pandas as pd\ndf = pd.DataFrame()",
            ["pandas"]
        ),
        (
            "import numpy as np\nimport matplotlib.pyplot as plt",
            ["numpy", "matplotlib"]
        ),
        (
            "from openpyxl import Workbook",
            ["openpyxl"]
        ),
        (
            "import pandas\nimport openpyxl\nimport xlsxwriter",
            ["pandas", "openpyxl", "xlsxwriter"]
        ),
        (
            "from docx import Document",
            ["python-docx"]
        ),
        (
            "from reportlab.lib.pagesizes import letter",
            ["reportlab"]
        ),
        (
            "from pptx import Presentation",
            ["python-pptx"]
        ),
        (
            "from PIL import Image",
            ["pillow"]
        ),
        (
            "import seaborn as sns",
            ["seaborn"]
        ),
        (
            "print('hello')",  # No libraries
            []
        ),
    ]

    for code, expected in test_cases:
        detected = detect_libraries_from_code(code)
        # Check if all expected libraries are detected
        missing = [lib for lib in expected if lib not in detected]
        if not missing:
            test_passed(f"Detected libraries: {detected}")
        else:
            all_passed = test_failed(f"Library detection", f"Missing {missing} in {detected}")

    return all_passed


# ============================================================
# 3. OUTPUT FILE DETECTION TESTS
# ============================================================

def test_output_file_detection():
    section("3. OUTPUT FILE DETECTION TESTS")

    all_passed = True

    test_cases = [
        # (code, expected_files)
        (
            "df.to_excel('report.xlsx')",
            ["report.xlsx"]
        ),
        (
            "df.to_csv('data.csv')",
            ["data.csv"]
        ),
        (
            "plt.savefig('chart.png')",
            ["chart.png"]
        ),
        (
            "doc.save('document.docx')",
            ["document.docx"]
        ),
        (
            "c.save('file.pdf')",
            ["file.pdf"]
        ),
        (
            "prs.save('slides.pptx')",
            ["slides.pptx"]
        ),
        (
            "df.to_excel('dados.xlsx')\nplt.savefig('grafico.png')",
            ["dados.xlsx", "grafico.png"]
        ),
        (
            "print('hello')",  # No output files
            []
        ),
        # Double quotes
        (
            'df.to_excel("output.xlsx")',
            ["output.xlsx"]
        ),
    ]

    for code, expected in test_cases:
        detected = detect_output_files_from_code(code)
        # Check if all expected files are detected
        missing = [f for f in expected if f not in detected]
        if not missing:
            test_passed(f"Detected files: {detected}")
        else:
            all_passed = test_failed(f"File detection", f"Missing {missing} in {detected}")

    return all_passed


# ============================================================
# 4. EXECUTOR CONFIG TESTS
# ============================================================

def test_executor_config():
    section("4. EXECUTOR CONFIG TESTS")

    all_passed = True

    config = CodeExecutorConfig()

    # Test default values
    if config.timeout_seconds == 60:
        test_passed("Default timeout is 60 seconds")
    else:
        all_passed = test_failed("Default timeout", f"Expected 60, got {config.timeout_seconds}")

    if config.max_memory_mb == 512:
        test_passed("Default memory is 512 MB")
    else:
        all_passed = test_failed("Default memory", f"Expected 512, got {config.max_memory_mb}")

    # Test allowed libraries
    required_libs = ["pandas", "numpy", "matplotlib", "openpyxl", "python-docx", "reportlab"]
    for lib in required_libs:
        if lib in config.allowed_libraries:
            test_passed(f"Library allowed: {lib}")
        else:
            all_passed = test_failed(f"Library not allowed", lib)

    return all_passed


# ============================================================
# 5. E2B INTEGRATION TESTS (requires E2B API key)
# ============================================================

async def test_e2b_integration():
    section("5. E2B INTEGRATION TESTS")

    # Check if E2B is configured
    mode = os.getenv("EXECUTOR_MODE", "local")
    api_key = os.getenv("E2B_API_KEY", "")

    if mode != "e2b" or not api_key:
        print("   [SKIP] E2B not configured (EXECUTOR_MODE != e2b or no API key)")
        return True

    all_passed = True

    # Test 5.1: Simple print
    print("\n   Testing simple code execution...")
    result = await code_executor.execute(
        code="print(2 + 2)",
        libraries=[],
        output_files=[]
    )

    if result.status == ExecutionStatus.SUCCESS and "4" in result.stdout:
        test_passed("Simple print: 2+2=4")
    else:
        all_passed = test_failed("Simple print", f"Status: {result.status}, stdout: {result.stdout}")

    # Test 5.2: Library import
    print("\n   Testing library import (pandas)...")
    result = await code_executor.execute(
        code="import pandas as pd\nprint(pd.__version__)",
        libraries=["pandas"],
        output_files=[]
    )

    if result.status == ExecutionStatus.SUCCESS:
        test_passed(f"Pandas import: version {result.stdout.strip()}")
    else:
        all_passed = test_failed("Pandas import", f"Status: {result.status}, stderr: {result.stderr}")

    # Test 5.3: File generation (Excel)
    print("\n   Testing Excel file generation...")
    excel_code = """
import pandas as pd
df = pd.DataFrame({
    'Nome': ['Alice', 'Bob', 'Carol'],
    'Nota': [95, 87, 92]
})
df.to_excel('notas.xlsx', index=False)
print('Excel created!')
"""
    result = await code_executor.execute(
        code=excel_code,
        libraries=["pandas", "openpyxl"],
        output_files=["notas.xlsx"]
    )

    if result.status == ExecutionStatus.SUCCESS and len(result.files_generated) > 0:
        file = result.files_generated[0]
        test_passed(f"Excel generated: {file.filename} ({file.size_bytes} bytes)")
    else:
        all_passed = test_failed("Excel generation", f"Status: {result.status}, files: {len(result.files_generated)}")

    # Test 5.4: Matplotlib chart
    print("\n   Testing Matplotlib chart generation...")
    chart_code = """
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

plt.figure(figsize=(8, 6))
plt.plot([1, 2, 3, 4], [1, 4, 2, 3])
plt.title('Test Chart')
plt.savefig('chart.png', dpi=100)
print('Chart saved!')
"""
    result = await code_executor.execute(
        code=chart_code,
        libraries=["matplotlib"],
        output_files=["chart.png"]
    )

    if result.status == ExecutionStatus.SUCCESS and len(result.files_generated) > 0:
        file = result.files_generated[0]
        test_passed(f"Chart generated: {file.filename} ({file.size_bytes} bytes)")
    else:
        all_passed = test_failed("Chart generation", f"Status: {result.status}, files: {len(result.files_generated)}")

    # Test 5.5: Security violation should be blocked
    print("\n   Testing security violation blocking...")
    result = await code_executor.execute(
        code="import os\nos.system('ls')",
        libraries=[],
        output_files=[]
    )

    if result.status == ExecutionStatus.SECURITY_VIOLATION:
        test_passed("Security violation blocked")
    else:
        all_passed = test_failed("Security blocking", f"Expected SECURITY_VIOLATION, got {result.status}")

    # Test 5.6: Check availability
    print("\n   Testing availability check...")
    available, message = await code_executor.check_availability()

    if available:
        test_passed(f"Availability check: {message}")
    else:
        all_passed = test_failed("Availability check", message)

    return all_passed


# ============================================================
# 6. API ENDPOINT TESTS (requires server running)
# ============================================================

async def test_api_endpoints():
    section("6. API ENDPOINT TESTS")

    try:
        import httpx
    except ImportError:
        print("   [SKIP] httpx not installed (pip install httpx)")
        return True

    base_url = "http://localhost:8000"

    # Check if server is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}/api/code/status", timeout=5.0)
    except Exception as e:
        print(f"   [SKIP] Server not running at {base_url}: {e}")
        return True

    all_passed = True

    async with httpx.AsyncClient() as client:
        # Test 6.1: Status endpoint
        print("\n   Testing GET /api/code/status...")
        response = await client.get(f"{base_url}/api/code/status")
        if response.status_code == 200:
            data = response.json()
            test_passed(f"Status endpoint: mode={data['mode']}, available={data['available']}")
        else:
            all_passed = test_failed("Status endpoint", f"Status code: {response.status_code}")

        # Test 6.2: Libraries endpoint
        print("\n   Testing GET /api/code/libraries...")
        response = await client.get(f"{base_url}/api/code/libraries")
        if response.status_code == 200:
            data = response.json()
            test_passed(f"Libraries endpoint: {len(data['allowed_libraries'])} libraries")
        else:
            all_passed = test_failed("Libraries endpoint", f"Status code: {response.status_code}")

        # Test 6.3: Validate endpoint (safe code)
        print("\n   Testing POST /api/code/validate (safe code)...")
        response = await client.post(
            f"{base_url}/api/code/validate",
            json={"code": "print('hello')"}
        )
        if response.status_code == 200:
            data = response.json()
            if data['is_safe']:
                test_passed("Validate endpoint: safe code accepted")
            else:
                all_passed = test_failed("Validate endpoint", f"Safe code rejected: {data['violations']}")
        else:
            all_passed = test_failed("Validate endpoint", f"Status code: {response.status_code}")

        # Test 6.4: Validate endpoint (dangerous code)
        print("\n   Testing POST /api/code/validate (dangerous code)...")
        response = await client.post(
            f"{base_url}/api/code/validate",
            json={"code": "import os\nos.system('ls')"}
        )
        if response.status_code == 200:
            data = response.json()
            if not data['is_safe']:
                test_passed("Validate endpoint: dangerous code blocked")
            else:
                all_passed = test_failed("Validate endpoint", "Dangerous code not blocked")
        else:
            all_passed = test_failed("Validate endpoint", f"Status code: {response.status_code}")

        # Test 6.5: Detect endpoint
        print("\n   Testing POST /api/code/detect...")
        response = await client.post(
            f"{base_url}/api/code/detect",
            json={"code": "import pandas as pd\ndf.to_excel('out.xlsx')"}
        )
        if response.status_code == 200:
            data = response.json()
            test_passed(f"Detect endpoint: libs={data['detected_libraries']}, files={data['detected_output_files']}")
        else:
            all_passed = test_failed("Detect endpoint", f"Status code: {response.status_code}")

        # Test 6.6: Execute endpoint
        print("\n   Testing POST /api/code/execute...")
        response = await client.post(
            f"{base_url}/api/code/execute",
            json={"code": "print(10 * 5)", "auto_detect": True},
            timeout=30.0
        )
        if response.status_code == 200:
            data = response.json()
            if data['status'] == 'success' and '50' in data['stdout']:
                test_passed(f"Execute endpoint: 10*5={data['stdout'].strip()}")
            else:
                all_passed = test_failed("Execute endpoint", f"Status: {data['status']}, stdout: {data['stdout']}")
        else:
            all_passed = test_failed("Execute endpoint", f"Status code: {response.status_code}")

    return all_passed


# ============================================================
# MAIN
# ============================================================

async def main():
    print("\n" + "="*60)
    print(" CODE EXECUTOR TESTS")
    print("="*60)

    results = {}

    # Unit tests (always run)
    results["Security Validator"] = test_security_validator()
    results["Library Detection"] = test_library_detection()
    results["Output File Detection"] = test_output_file_detection()
    results["Executor Config"] = test_executor_config()

    # Integration tests (require E2B or server)
    results["E2B Integration"] = await test_e2b_integration()
    results["API Endpoints"] = await test_api_endpoints()

    # Summary
    print("\n" + "="*60)
    print(" TEST SUMMARY")
    print("="*60)

    all_passed = True
    for name, passed in results.items():
        status = "[OK]" if passed else "[FAIL]"
        print(f"   {status} {name}")
        if not passed:
            all_passed = False

    print("\n" + "="*60)
    if all_passed:
        print(" ALL TESTS PASSED!")
    else:
        print(" SOME TESTS FAILED")
    print("="*60 + "\n")

    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
