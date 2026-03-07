"""
Seed Live Test Data — Creates test materia, turmas, alunos, atividades, and documents
on the live Prova AI deployment via HTTP API calls.

Usage:
    python scripts/seed_live_test_data.py
    python scripts/seed_live_test_data.py --url http://localhost:8000
    python scripts/seed_live_test_data.py --url https://ia-educacao-v2.onrender.com

Produces: scripts/seed_output.json with all created entity IDs.
"""

import argparse
import json
import sys
import os
import tempfile
from pathlib import Path
from datetime import datetime

try:
    import httpx
except ImportError:
    print("httpx not installed. Run: pip install httpx")
    sys.exit(1)


DEFAULT_URL = "https://ia-educacao-v2.onrender.com"
OUTPUT_FILE = Path(__file__).parent / "seed_output.json"

MATERIA_NAME = "Teste Verificação"
TURMAS = [
    {"nome": "Turma Alpha", "periodo": "2026.1"},
    {"nome": "Turma Beta", "periodo": "2026.1"},
]
ALUNOS = [
    # Turma Alpha
    [
        {"nome": "Ana Silva", "email": "ana.silva@teste.com", "matricula": "T001"},
        {"nome": "Carlos Oliveira", "email": "carlos.oliveira@teste.com", "matricula": "T002"},
    ],
    # Turma Beta
    [
        {"nome": "Julia Santos", "email": "julia.santos@teste.com", "matricula": "T003"},
        {"nome": "Pedro Lima", "email": "pedro.lima@teste.com", "matricula": "T004"},
    ],
]
ATIVIDADES = [
    {"nome": "Prova 1 - Álgebra Básica", "tipo": "prova", "nota_maxima": 10.0},
    {"nome": "Prova 2 - Geometria Plana", "tipo": "prova", "nota_maxima": 10.0},
]

# --- Document content templates ---

ENUNCIADO_TEMPLATE = """PROVA DE MATEMÁTICA — {atividade}
Matéria: {materia} | Turma: {turma}
Data: {data}

Questão 1 (2,5 pontos):
Resolva a equação: 3x + 7 = 22

Questão 2 (2,5 pontos):
Simplifique a expressão: (2x + 3)(x - 1)

Questão 3 (2,5 pontos):
Calcule a área de um triângulo com base 8cm e altura 5cm.

Questão 4 (2,5 pontos):
Se f(x) = 2x² - 3x + 1, encontre f(2).
"""

GABARITO_TEMPLATE = """GABARITO — {atividade}
Matéria: {materia} | Turma: {turma}

Questão 1: x = 5 (3x + 7 = 22 → 3x = 15 → x = 5)
Questão 2: 2x² + x - 3 (distributiva: 2x·x + 2x·(-1) + 3·x + 3·(-1))
Questão 3: 20 cm² (A = b·h/2 = 8·5/2 = 20)
Questão 4: f(2) = 3 (2·4 - 3·2 + 1 = 8 - 6 + 1 = 3)
"""

PROVA_ALUNO_TEMPLATES = {
    "excelente": """Nome: {aluno}

Questão 1: x = 5. Subtraí 7 dos dois lados: 3x = 15, dividi por 3: x = 5.
Questão 2: 2x² + x - 3. Apliquei distributiva: 2x·x = 2x², 2x·(-1) = -2x, 3·x = 3x, 3·(-1) = -3. Somando: 2x² + x - 3.
Questão 3: Área = 20 cm². Usei a fórmula A = base × altura / 2 = 8 × 5 / 2 = 20.
Questão 4: f(2) = 3. Substituí x=2: 2(4) - 3(2) + 1 = 8 - 6 + 1 = 3.
""",
    "medio": """Nome: {aluno}

Questão 1: x = 5. 3x = 15, x = 5.
Questão 2: 2x² - 3. Não tenho certeza se está certo.
Questão 3: 40 cm². A = 8 × 5 = 40.
Questão 4: f(2) = 3. 2×4 - 6 + 1 = 3.
""",
    "ruim": """Nome: {aluno}

Questão 1: x = 7. Acho que é 22 - 7 = 15 dividido por alguma coisa.
Questão 2: Não sei fazer esta.
Questão 3: 13 cm². Somei a base com a altura: 8 + 5 = 13.
Questão 4: Deixei em branco.
""",
}

# Quality assignments per student (deterministic)
STUDENT_QUALITIES = ["excelente", "medio", "excelente", "ruim"]


class LiveSeeder:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.api = f"{self.base_url}/api"
        self.client = httpx.Client(timeout=60.0)
        self.output = {
            "url": self.base_url,
            "created_at": datetime.now().isoformat(),
            "materia_id": None,
            "turmas": [],
            "alunos": [],
            "atividades": [],
            "documents": [],
        }

    def log(self, msg: str):
        print(f"  {msg}")

    def post_json(self, path: str, data: dict) -> dict:
        url = f"{self.api}{path}"
        resp = self.client.post(url, json=data)
        resp.raise_for_status()
        return resp.json()

    def post_form(self, path: str, data: dict) -> dict:
        url = f"{self.api}{path}"
        resp = self.client.post(url, data=data)
        resp.raise_for_status()
        return resp.json()

    def upload_file(self, path: str, file_path: str, fields: dict) -> dict:
        url = f"{self.api}{path}"
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "text/plain")}
            resp = self.client.post(url, files=files, data=fields)
        resp.raise_for_status()
        return resp.json()

    def get(self, path: str) -> dict:
        url = f"{self.api}{path}"
        resp = self.client.get(url)
        resp.raise_for_status()
        return resp.json()

    def check_existing(self) -> bool:
        """Check if test materia already exists. If so, load turma IDs too."""
        data = self.get("/materias")
        materias = data.get("materias", data) if isinstance(data, dict) else data
        for m in materias:
            if isinstance(m, dict) and m.get("nome") == MATERIA_NAME:
                materia_id = m["id"]
                print(f"  Test materia '{MATERIA_NAME}' already exists (id={materia_id}).")
                self.output["materia_id"] = materia_id

                # Load existing turmas
                turma_data = self.get(f"/turmas?materia_id={materia_id}")
                turmas_list = turma_data.get("turmas", turma_data) if isinstance(turma_data, dict) else turma_data
                for t in turmas_list:
                    if isinstance(t, dict):
                        self.output["turmas"].append({"id": t["id"], "nome": t["nome"]})
                        print(f"  Found turma: {t['nome']} (id={t['id']})")

                # Check if alunos already exist
                for turma_info in self.output["turmas"]:
                    aluno_data = self.get(f"/alunos?turma_id={turma_info['id']}")
                    alunos_list = aluno_data.get("alunos", aluno_data) if isinstance(aluno_data, dict) else aluno_data
                    if alunos_list:
                        for a in alunos_list:
                            if isinstance(a, dict):
                                self.output["alunos"].append({
                                    "id": a["id"],
                                    "nome": a["nome"],
                                    "turma_id": turma_info["id"],
                                    "turma_nome": turma_info["nome"],
                                })
                                print(f"  Found aluno: {a['nome']} in {turma_info['nome']}")

                # Check if atividades already exist
                for turma_info in self.output["turmas"]:
                    ativ_data = self.get(f"/atividades?turma_id={turma_info['id']}")
                    ativ_list = ativ_data.get("atividades", ativ_data) if isinstance(ativ_data, dict) else ativ_data
                    if ativ_list:
                        for at in ativ_list:
                            if isinstance(at, dict):
                                self.output["atividades"].append({
                                    "id": at["id"],
                                    "nome": at["nome"],
                                    "turma_id": turma_info["id"],
                                    "turma_nome": turma_info["nome"],
                                })
                                print(f"  Found atividade: {at['nome']} in {turma_info['nome']}")

                return True
        return False

    def create_materia(self):
        print("\n1. Creating materia...")
        result = self.post_json("/materias", {
            "nome": MATERIA_NAME,
            "descricao": "Matéria de teste para verificação de relatórios",
            "nivel": "fundamental_2",
        })
        materia_id = result["materia"]["id"]
        self.output["materia_id"] = materia_id
        self.log(f"Created: {MATERIA_NAME} (id={materia_id})")
        return materia_id

    def create_turmas(self, materia_id: str):
        print("\n2. Creating turmas...")
        for turma_cfg in TURMAS:
            result = self.post_json("/turmas", {
                "materia_id": materia_id,
                "nome": turma_cfg["nome"],
                "ano_letivo": 2026,
                "periodo": turma_cfg["periodo"],
                "descricao": f"Turma de teste — {turma_cfg['nome']}",
            })
            turma_id = result["turma"]["id"]
            self.output["turmas"].append({"id": turma_id, "nome": turma_cfg["nome"]})
            self.log(f"Created: {turma_cfg['nome']} (id={turma_id})")

    def create_alunos(self):
        print("\n3. Creating alunos and linking to turmas...")
        for turma_idx, turma_alunos in enumerate(ALUNOS):
            turma_id = self.output["turmas"][turma_idx]["id"]
            turma_nome = self.output["turmas"][turma_idx]["nome"]
            for aluno_cfg in turma_alunos:
                # Create student
                result = self.post_json("/alunos", {
                    "nome": aluno_cfg["nome"],
                    "email": aluno_cfg["email"],
                    "matricula": aluno_cfg["matricula"],
                })
                aluno_id = result["aluno"]["id"]

                # Link to turma
                self.post_json("/alunos/vincular", {
                    "aluno_id": aluno_id,
                    "turma_id": turma_id,
                })

                self.output["alunos"].append({
                    "id": aluno_id,
                    "nome": aluno_cfg["nome"],
                    "turma_id": turma_id,
                    "turma_nome": turma_nome,
                })
                self.log(f"Created + linked: {aluno_cfg['nome']} -> {turma_nome}")

    def create_missing_alunos(self):
        """Create only alunos that don't already exist (by name)."""
        existing_names = {a["nome"] for a in self.output["alunos"]}
        for turma_idx, turma_alunos in enumerate(ALUNOS):
            turma_id = self.output["turmas"][turma_idx]["id"]
            turma_nome = self.output["turmas"][turma_idx]["nome"]
            for aluno_cfg in turma_alunos:
                if aluno_cfg["nome"] in existing_names:
                    continue
                result = self.post_json("/alunos", {
                    "nome": aluno_cfg["nome"],
                    "email": aluno_cfg["email"],
                    "matricula": aluno_cfg["matricula"],
                })
                aluno_id = result["aluno"]["id"]
                self.post_json("/alunos/vincular", {
                    "aluno_id": aluno_id,
                    "turma_id": turma_id,
                })
                self.output["alunos"].append({
                    "id": aluno_id,
                    "nome": aluno_cfg["nome"],
                    "turma_id": turma_id,
                    "turma_nome": turma_nome,
                })
                self.log(f"Created + linked: {aluno_cfg['nome']} -> {turma_nome}")

    def create_atividades(self):
        print("\n4. Creating atividades...")
        for turma_info in self.output["turmas"]:
            turma_id = turma_info["id"]
            turma_nome = turma_info["nome"]
            for ativ_cfg in ATIVIDADES:
                result = self.post_json("/atividades", {
                    "turma_id": turma_id,
                    "nome": ativ_cfg["nome"],
                    "tipo": ativ_cfg["tipo"],
                    "nota_maxima": ativ_cfg["nota_maxima"],
                    "descricao": f"Atividade de teste para {turma_nome}",
                })
                ativ_id = result["atividade"]["id"]
                self.output["atividades"].append({
                    "id": ativ_id,
                    "nome": ativ_cfg["nome"],
                    "turma_id": turma_id,
                    "turma_nome": turma_nome,
                })
                self.log(f"Created: {ativ_cfg['nome']} in {turma_nome} (id={ativ_id})")

    def upload_documents(self):
        print("\n5. Uploading documents (enunciados, gabaritos, provas)...")
        tmp_dir = Path(tempfile.mkdtemp(prefix="seed_"))

        for ativ_info in self.output["atividades"]:
            ativ_id = ativ_info["id"]
            ativ_nome = ativ_info["nome"]
            turma_nome = ativ_info["turma_nome"]

            # Enunciado
            enunciado_content = ENUNCIADO_TEMPLATE.format(
                atividade=ativ_nome,
                materia=MATERIA_NAME,
                turma=turma_nome,
                data=datetime.now().strftime("%d/%m/%Y"),
            )
            enunciado_path = tmp_dir / f"enunciado_{ativ_id}.txt"
            enunciado_path.write_text(enunciado_content, encoding="utf-8")

            result = self.upload_file("/documentos/upload", str(enunciado_path), {
                "tipo": "enunciado",
                "atividade_id": ativ_id,
            })
            doc_id = result["documento"]["id"]
            self.output["documents"].append({"id": doc_id, "tipo": "enunciado", "atividade_id": ativ_id})
            self.log(f"Uploaded enunciado for {ativ_nome} (id={doc_id})")

            # Gabarito
            gabarito_content = GABARITO_TEMPLATE.format(
                atividade=ativ_nome,
                materia=MATERIA_NAME,
                turma=turma_nome,
            )
            gabarito_path = tmp_dir / f"gabarito_{ativ_id}.txt"
            gabarito_path.write_text(gabarito_content, encoding="utf-8")

            result = self.upload_file("/documentos/upload", str(gabarito_path), {
                "tipo": "gabarito",
                "atividade_id": ativ_id,
            })
            doc_id = result["documento"]["id"]
            self.output["documents"].append({"id": doc_id, "tipo": "gabarito", "atividade_id": ativ_id})
            self.log(f"Uploaded gabarito for {ativ_nome} (id={doc_id})")

            # Student submissions (provas respondidas)
            turma_alunos = [a for a in self.output["alunos"] if a["turma_id"] == ativ_info["turma_id"]]
            for i, aluno_info in enumerate(turma_alunos):
                quality = STUDENT_QUALITIES[i % len(STUDENT_QUALITIES)]
                prova_content = PROVA_ALUNO_TEMPLATES[quality].format(aluno=aluno_info["nome"])

                prova_path = tmp_dir / f"prova_{ativ_id}_{aluno_info['id']}.txt"
                prova_path.write_text(prova_content, encoding="utf-8")

                result = self.upload_file("/documentos/upload", str(prova_path), {
                    "tipo": "prova_respondida",
                    "atividade_id": ativ_id,
                    "aluno_id": aluno_info["id"],
                })
                doc_id = result["documento"]["id"]
                self.output["documents"].append({
                    "id": doc_id,
                    "tipo": "prova_respondida",
                    "atividade_id": ativ_id,
                    "aluno_id": aluno_info["id"],
                    "quality": quality,
                })
                self.log(f"Uploaded prova ({quality}) for {aluno_info['nome']} — {ativ_nome}")

        # Cleanup temp files
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)

    def save_output(self):
        OUTPUT_FILE.write_text(json.dumps(self.output, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nOutput saved to: {OUTPUT_FILE}")

    def print_summary(self):
        print("\n" + "=" * 60)
        print("SEED SUMMARY")
        print("=" * 60)
        print(f"  URL:         {self.base_url}")
        print(f"  Materia:     {MATERIA_NAME} ({self.output['materia_id']})")
        print(f"  Turmas:      {len(self.output['turmas'])}")
        print(f"  Alunos:      {len(self.output['alunos'])}")
        print(f"  Atividades:  {len(self.output['atividades'])}")
        print(f"  Documents:   {len(self.output['documents'])}")
        print(f"  Output file: {OUTPUT_FILE}")
        print("=" * 60)

    def run(self):
        print(f"Seeding test data on: {self.base_url}")

        # Check connectivity
        try:
            health = self.client.get(f"{self.api}/health")
            print(f"  Health check: {health.status_code} — {health.json().get('status', 'unknown')}")
        except Exception as e:
            print(f"  Cannot reach {self.base_url}: {e}")
            sys.exit(1)

        # Check existing data and resume from where we left off
        exists = self.check_existing()

        materia_id = self.output["materia_id"]
        if not exists:
            materia_id = self.create_materia()
            self.create_turmas(materia_id)
        elif not self.output["turmas"]:
            self.create_turmas(materia_id)

        expected_alunos = sum(len(turma_alunos) for turma_alunos in ALUNOS)
        if len(self.output["alunos"]) < expected_alunos:
            print(f"\n3. Found {len(self.output['alunos'])}/{expected_alunos} alunos. Creating missing ones...")
            self.create_missing_alunos()
        else:
            print(f"\n3. Alunos already exist ({len(self.output['alunos'])} found). Skipping.")

        if not self.output["atividades"]:
            self.create_atividades()
        else:
            print(f"\n4. Atividades already exist ({len(self.output['atividades'])} found). Skipping.")

        # Always try to upload documents (idempotent — will create new ones)
        if not self.output["alunos"] or not self.output["atividades"]:
            print("\nCannot upload documents without alunos and atividades.")
        else:
            self.upload_documents()

        self.save_output()
        self.print_summary()


def main():
    parser = argparse.ArgumentParser(description="Seed test data on live Prova AI")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"Base URL (default: {DEFAULT_URL})")
    args = parser.parse_args()

    seeder = LiveSeeder(args.url)
    seeder.run()


if __name__ == "__main__":
    main()
