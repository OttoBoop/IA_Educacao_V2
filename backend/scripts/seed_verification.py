"""
Seed Verification Dataset — One-time script to create dedicated test data
for the Full Pipeline Journey Verification suite.

Creates:
- 1 materia: "Matemática-V" (verification suffix)
- 2 turmas: "Alpha-V", "Beta-V"
- 4 alunos: "Ana Verifica", "Bruno Verifica", "Carla Verifica", "Daniel Verifica"
- 2 atividades per turma (4 total)
- For each atividade: 1 enunciado, 1 gabarito, 2 student submissions

Idempotent: checks for existing entities by name before creating.

Usage:
    python -m scripts.seed_verification [--url URL] [--dry-run]
"""

import argparse
import json
import sys
import tempfile
import textwrap
from datetime import datetime
from pathlib import Path

import httpx

DEFAULT_URL = "https://ia-educacao-v2.onrender.com"
OUTPUT_FILE = Path(__file__).parent / "seed_verification_output.json"

# --- Data definitions ---

MATERIA = {"nome": "Matemática-V", "descricao": "Matéria de verificação do pipeline", "nivel": "fundamental_2"}

TURMAS = [
    {"nome": "Alpha-V", "ano_letivo": 2026, "periodo": "2026.1"},
    {"nome": "Beta-V", "ano_letivo": 2026, "periodo": "2026.1"},
]

ALUNOS = [
    {"nome": "Ana Verifica", "email": "ana.verifica@teste.com", "matricula": "V001"},
    {"nome": "Bruno Verifica", "email": "bruno.verifica@teste.com", "matricula": "V002"},
    {"nome": "Carla Verifica", "email": "carla.verifica@teste.com", "matricula": "V003"},
    {"nome": "Daniel Verifica", "email": "daniel.verifica@teste.com", "matricula": "V004"},
]

# 2 atividades per turma
ATIVIDADES_PER_TURMA = [
    {"nome_suffix": "Prova Álgebra-V", "tipo": "prova", "nota_maxima": 10.0},
    {"nome_suffix": "Prova Geometria-V", "tipo": "prova", "nota_maxima": 10.0},
]

# Which alunos go to which turma (index into ALUNOS)
TURMA_ALUNOS = {
    0: [0, 1],  # Alpha-V gets Ana, Bruno
    1: [2, 3],  # Beta-V gets Carla, Daniel
}


def make_enunciado(atividade_nome: str, materia_nome: str, turma_nome: str) -> str:
    if "Álgebra" in atividade_nome:
        return textwrap.dedent(f"""\
            PROVA DE {materia_nome.upper()} — {atividade_nome}
            Turma: {turma_nome}
            Data: {datetime.now().strftime('%d/%m/%Y')}

            Questão 1 (2,5 pontos):
            Resolva a equação: 3x + 7 = 22. Mostre todos os passos.

            Questão 2 (2,5 pontos):
            Simplifique a expressão: (2a + 3b) - (a - 2b) + 4a

            Questão 3 (2,5 pontos):
            Um retângulo tem perímetro de 30 cm. Se o comprimento é o dobro da largura, quais são as dimensões?

            Questão 4 (2,5 pontos):
            Resolva o sistema: x + y = 10 e 2x - y = 5
        """)
    else:
        return textwrap.dedent(f"""\
            PROVA DE {materia_nome.upper()} — {atividade_nome}
            Turma: {turma_nome}
            Data: {datetime.now().strftime('%d/%m/%Y')}

            Questão 1 (2,5 pontos):
            Calcule a área de um triângulo com base 8 cm e altura 5 cm.

            Questão 2 (2,5 pontos):
            Um círculo tem raio de 7 cm. Calcule seu perímetro (use pi = 3,14).

            Questão 3 (2,5 pontos):
            Classifique um triângulo com lados 3, 4 e 5 cm quanto aos lados e ângulos.

            Questão 4 (2,5 pontos):
            Calcule o volume de um cubo com aresta de 4 cm.
        """)


def make_gabarito(atividade_nome: str, materia_nome: str, turma_nome: str) -> str:
    if "Álgebra" in atividade_nome:
        return textwrap.dedent(f"""\
            GABARITO — {atividade_nome}
            Matéria: {materia_nome} | Turma: {turma_nome}

            Questão 1: x = 5
            Resolução: 3x + 7 = 22 -> 3x = 15 -> x = 5

            Questão 2: 5a + 5b
            Resolução: 2a + 3b - a + 2b + 4a = (2a - a + 4a) + (3b + 2b) = 5a + 5b

            Questão 3: Largura = 5 cm, Comprimento = 10 cm
            Resolução: 2(2l + l) = 30 -> 6l = 30 -> l = 5, c = 10

            Questão 4: x = 5, y = 5
            Resolução: x + y = 10, 2x - y = 5 -> 3x = 15 -> x = 5, y = 5
        """)
    else:
        return textwrap.dedent(f"""\
            GABARITO — {atividade_nome}
            Matéria: {materia_nome} | Turma: {turma_nome}

            Questão 1: Área = 20 cm²
            Resolução: A = (b × h) / 2 = (8 × 5) / 2 = 20

            Questão 2: Perímetro = 43,96 cm
            Resolução: C = 2pir = 2 × 3,14 × 7 = 43,96

            Questão 3: Escaleno (lados diferentes) e retângulo (3² + 4² = 5²)
            Resolução: Triângulo pitagórico clássico.

            Questão 4: Volume = 64 cm³
            Resolução: V = a³ = 4³ = 64
        """)


# Two quality levels for student submissions
STUDENT_ANSWERS = {
    "algebra_good": textwrap.dedent("""\
        Questão 1: 3x + 7 = 22 -> 3x = 15 -> x = 5
        Questão 2: 2a + 3b - a + 2b + 4a = 5a + 5b
        Questão 3: Perímetro = 2(c + l) = 30. Se c = 2l, então 2(2l + l) = 30, l = 5, c = 10.
        Questão 4: x + y = 10, 2x - y = 5. Somando: 3x = 15, x = 5, y = 5.
    """),
    "algebra_partial": textwrap.dedent("""\
        Questão 1: x = 5
        Questão 2: 2a + 3b (não terminei)
        Questão 3: Não sei como fazer
        Questão 4: x = 5 e y = 5
    """),
    "geometry_good": textwrap.dedent("""\
        Questão 1: A = (8 × 5) / 2 = 20 cm²
        Questão 2: C = 2 × 3,14 × 7 = 43,96 cm
        Questão 3: Escaleno (todos os lados diferentes) e retângulo (3² + 4² = 5²).
        Questão 4: V = 4³ = 64 cm³
    """),
    "geometry_partial": textwrap.dedent("""\
        Questão 1: Área = 40 cm² (esqueci de dividir por 2)
        Questão 2: C = 2 × 3,14 × 7 = 44 cm (arredondei)
        Questão 3: É isósceles (errei)
        Questão 4: V = 4 × 4 = 16 cm³ (confundi com área)
    """),
}


def get_submission_text(atividade_nome: str, aluno_idx_in_turma: int) -> str:
    """First student gets good answers, second gets partial."""
    quality = "good" if aluno_idx_in_turma == 0 else "partial"
    topic = "algebra" if "Álgebra" in atividade_nome else "geometry"
    return STUDENT_ANSWERS[f"{topic}_{quality}"]


class SeedVerification:
    def __init__(self, base_url: str, dry_run: bool = False):
        self.base_url = base_url.rstrip("/")
        self.api = f"{self.base_url}/api"
        self.dry_run = dry_run
        self.client = httpx.Client(timeout=60)
        self.output: dict = {"created_at": datetime.now().isoformat(), "entities": {}}

    def log(self, msg: str):
        print(f"  > {msg}")

    def check_health(self):
        print(f"Checking health at {self.api}/health ...")
        r = self.client.get(f"{self.api}/health")
        r.raise_for_status()
        print(f"  Health OK: {r.json()}")

    def find_existing(self, endpoint: str, name_field: str, name_value: str, **params):
        """Check if an entity already exists by name."""
        r = self.client.get(f"{self.api}/{endpoint}", params=params)
        r.raise_for_status()
        data = r.json()
        # API returns different list keys depending on endpoint
        items = data.get(endpoint, data.get("data", []))
        if isinstance(items, dict):
            items = items.get("items", [])
        for item in items:
            if item.get(name_field) == name_value:
                return item
        return None

    def create_materia(self) -> dict:
        print("\n[1/6] Creating materia...")
        existing = self.find_existing("materias", "nome", MATERIA["nome"])
        if existing:
            self.log(f"Already exists: {existing['nome']} (id={existing['id']})")
            self.output["entities"]["materia"] = existing
            return existing

        if self.dry_run:
            self.log(f"[DRY RUN] Would create materia: {MATERIA['nome']}")
            return {"id": "dry-run-materia", "nome": MATERIA["nome"]}

        r = self.client.post(f"{self.api}/materias", json=MATERIA)
        r.raise_for_status()
        materia = r.json()["materia"]
        self.log(f"Created: {materia['nome']} (id={materia['id']})")
        self.output["entities"]["materia"] = materia
        return materia

    def create_turmas(self, materia_id: str) -> list:
        print("\n[2/6] Creating turmas...")
        created = []
        for t_def in TURMAS:
            existing = self.find_existing("turmas", "nome", t_def["nome"], materia_id=materia_id)
            if existing:
                self.log(f"Already exists: {existing['nome']} (id={existing['id']})")
                created.append(existing)
                continue

            if self.dry_run:
                self.log(f"[DRY RUN] Would create turma: {t_def['nome']}")
                created.append({"id": f"dry-run-turma-{t_def['nome']}", "nome": t_def["nome"]})
                continue

            payload = {**t_def, "materia_id": materia_id}
            r = self.client.post(f"{self.api}/turmas", json=payload)
            r.raise_for_status()
            turma = r.json()["turma"]
            self.log(f"Created: {turma['nome']} (id={turma['id']})")
            created.append(turma)

        self.output["entities"]["turmas"] = created
        return created

    def create_alunos_and_bind(self, turmas: list) -> list:
        print("\n[3/6] Creating alunos and binding to turmas...")
        created = []
        for i, a_def in enumerate(ALUNOS):
            existing = self.find_existing("alunos", "nome", a_def["nome"])
            if existing:
                self.log(f"Already exists: {existing['nome']} (id={existing['id']})")
                created.append(existing)
            elif self.dry_run:
                self.log(f"[DRY RUN] Would create aluno: {a_def['nome']}")
                created.append({"id": f"dry-run-aluno-{i}", "nome": a_def["nome"]})
            else:
                r = self.client.post(f"{self.api}/alunos", json=a_def)
                r.raise_for_status()
                aluno = r.json()["aluno"]
                self.log(f"Created: {aluno['nome']} (id={aluno['id']})")
                created.append(aluno)

        # Bind alunos to turmas
        print("\n[3b/6] Binding alunos to turmas...")
        for turma_idx, aluno_indices in TURMA_ALUNOS.items():
            turma = turmas[turma_idx]
            for ai in aluno_indices:
                aluno = created[ai]
                if self.dry_run:
                    self.log(f"[DRY RUN] Would bind {aluno['nome']} -> {turma['nome']}")
                    continue
                try:
                    r = self.client.post(
                        f"{self.api}/alunos/vincular",
                        json={"aluno_id": aluno["id"], "turma_id": turma["id"]},
                    )
                    r.raise_for_status()
                    self.log(f"Bound: {aluno['nome']} -> {turma['nome']}")
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 409 or "já vinculado" in e.response.text.lower():
                        self.log(f"Already bound: {aluno['nome']} -> {turma['nome']}")
                    else:
                        raise

        self.output["entities"]["alunos"] = created
        return created

    def create_atividades(self, turmas: list) -> list:
        print("\n[4/6] Creating atividades...")
        all_atividades = []
        for turma in turmas:
            turma_atividades = []
            for at_def in ATIVIDADES_PER_TURMA:
                nome = at_def["nome_suffix"]
                existing = self.find_existing("atividades", "nome", nome, turma_id=turma["id"])
                if existing:
                    self.log(f"Already exists: {existing['nome']} in {turma['nome']} (id={existing['id']})")
                    turma_atividades.append(existing)
                    continue

                if self.dry_run:
                    self.log(f"[DRY RUN] Would create atividade: {nome} in {turma['nome']}")
                    turma_atividades.append({"id": f"dry-run-at-{nome}", "nome": nome})
                    continue

                payload = {
                    "turma_id": turma["id"],
                    "nome": nome,
                    "tipo": at_def["tipo"],
                    "nota_maxima": at_def["nota_maxima"],
                }
                r = self.client.post(f"{self.api}/atividades", json=payload)
                r.raise_for_status()
                ativ = r.json()["atividade"]
                self.log(f"Created: {ativ['nome']} in {turma['nome']} (id={ativ['id']})")
                turma_atividades.append(ativ)
            all_atividades.append(turma_atividades)

        self.output["entities"]["atividades"] = all_atividades
        return all_atividades

    def upload_doc(self, atividade_id: str, tipo: str, content: str, filename: str, aluno_id: str = None):
        """Upload a text document as a file."""
        if self.dry_run:
            self.log(f"[DRY RUN] Would upload {tipo}: {filename}")
            return {"id": f"dry-run-doc-{filename}", "tipo": tipo}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(content)
            tmp_path = f.name

        try:
            with open(tmp_path, "rb") as fh:
                files = {"file": (filename, fh, "text/plain")}
                data = {"tipo": tipo, "atividade_id": atividade_id}
                if aluno_id:
                    data["aluno_id"] = aluno_id
                r = self.client.post(f"{self.api}/documentos/upload", files=files, data=data)
                r.raise_for_status()
                doc = r.json()["documento"]
                self.log(f"Uploaded {tipo}: {filename} (id={doc['id']})")
                return doc
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def upload_documents(self, turmas: list, all_atividades: list, alunos: list):
        print("\n[5/6] Uploading enunciados + gabaritos...")
        materia_nome = MATERIA["nome"]
        docs_created = []

        for turma_idx, turma in enumerate(turmas):
            turma_atividades = all_atividades[turma_idx]
            for ativ in turma_atividades:
                ativ_id = ativ["id"]
                ativ_nome = ativ["nome"]

                # Check if docs already exist for this atividade
                existing_docs = []
                if not self.dry_run:
                    r = self.client.get(f"{self.api}/documentos", params={"atividade_id": ativ_id})
                    if r.status_code == 200:
                        existing_docs = r.json().get("documentos", [])
                existing_tipos = {d.get("tipo") for d in existing_docs}

                # Enunciado
                if "enunciado" not in existing_tipos:
                    content = make_enunciado(ativ_nome, materia_nome, turma["nome"])
                    doc = self.upload_doc(ativ_id, "enunciado", content, f"enunciado_{ativ_nome}.txt")
                    docs_created.append(doc)
                else:
                    self.log(f"Enunciado already exists for {ativ_nome}")

                # Gabarito
                if "gabarito" not in existing_tipos:
                    content = make_gabarito(ativ_nome, materia_nome, turma["nome"])
                    doc = self.upload_doc(ativ_id, "gabarito", content, f"gabarito_{ativ_nome}.txt")
                    docs_created.append(doc)
                else:
                    self.log(f"Gabarito already exists for {ativ_nome}")

        print("\n[6/6] Uploading student submissions...")
        for turma_idx, turma in enumerate(turmas):
            turma_atividades = all_atividades[turma_idx]
            aluno_indices = TURMA_ALUNOS[turma_idx]

            for ativ in turma_atividades:
                ativ_id = ativ["id"]
                ativ_nome = ativ["nome"]

                # Check existing submissions
                existing_docs = []
                if not self.dry_run:
                    r = self.client.get(f"{self.api}/documentos", params={"atividade_id": ativ_id})
                    if r.status_code == 200:
                        existing_docs = r.json().get("documentos", [])
                existing_aluno_ids = {
                    d.get("aluno_id") for d in existing_docs if d.get("tipo") == "prova_respondida"
                }

                for local_idx, ai in enumerate(aluno_indices):
                    aluno = alunos[ai]
                    if aluno["id"] in existing_aluno_ids:
                        self.log(f"Submission already exists: {aluno['nome']} -> {ativ_nome}")
                        continue

                    header = f"Nome: {aluno['nome']}\n\n"
                    body = get_submission_text(ativ_nome, local_idx)
                    content = header + body
                    filename = f"prova_{aluno['nome']}_{ativ_nome}.txt"
                    doc = self.upload_doc(ativ_id, "prova_respondida", content, filename, aluno_id=aluno["id"])
                    docs_created.append(doc)

        self.output["entities"]["documents_created"] = len(docs_created)
        return docs_created

    def save_output(self):
        if self.dry_run:
            print("\n[DRY RUN] Would save output to", OUTPUT_FILE)
            return
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(self.output, f, indent=2, ensure_ascii=False, default=str)
        print(f"\nOutput saved to: {OUTPUT_FILE}")

    def run(self):
        print(f"{'='*60}")
        print(f"Seed Verification Dataset")
        print(f"Target: {self.base_url}")
        print(f"Dry run: {self.dry_run}")
        print(f"{'='*60}")

        self.check_health()

        materia = self.create_materia()
        turmas = self.create_turmas(materia["id"])
        alunos = self.create_alunos_and_bind(turmas)
        all_atividades = self.create_atividades(turmas)
        self.upload_documents(turmas, all_atividades, alunos)
        self.save_output()

        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"{'='*60}")
        print(f"  Materia: {materia.get('nome', 'N/A')}")
        for i, t in enumerate(turmas):
            print(f"  Turma {i+1}: {t.get('nome', 'N/A')}")
        print(f"  Alunos: {len(alunos)}")
        atv_count = sum(len(ta) for ta in all_atividades)
        print(f"  Atividades: {atv_count}")
        print(f"  Documents created this run: {self.output['entities'].get('documents_created', 0)}")
        print(f"{'='*60}")
        print("Done!")


def main():
    parser = argparse.ArgumentParser(description="Seed verification dataset for pipeline testing")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"Base URL (default: {DEFAULT_URL})")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without executing")
    args = parser.parse_args()

    seeder = SeedVerification(base_url=args.url, dry_run=args.dry_run)
    try:
        seeder.run()
    except httpx.HTTPStatusError as e:
        print(f"\nHTTP Error: {e.response.status_code} — {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except httpx.ConnectError as e:
        print(f"\nConnection Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
