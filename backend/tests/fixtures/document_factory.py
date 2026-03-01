"""
NOVO CR - Fábrica de Documentos de Teste

Gera documentos de teste em diferentes formatos e qualidades
para testar robustez do pipeline.

Uso:
    factory = DocumentFactory(Path("temp_tests"))

    # Criar prova de teste
    prova = factory.criar_prova_teste("Matemática", num_questoes=4)

    # Criar cenário completo
    cenario = factory.criar_cenario_completo("Matemática", num_alunos=2)

    # Criar documento corrompido
    doc = factory.criar_documento_corrompido("json_invalido")
"""

import json
import random
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import uuid


class DocumentQuality(Enum):
    """Qualidade do documento gerado"""
    PERFECT = "perfect"       # Documento perfeito
    NORMAL = "normal"         # Alguma variação natural
    POOR = "poor"             # Baixa qualidade (OCR ruim, etc.)
    CORRUPTED = "corrupted"   # Corrompido propositalmente
    EMPTY = "empty"           # Vazio


class DocumentFormat(Enum):
    """Formato do documento"""
    TXT = ".txt"
    JSON = ".json"
    PDF = ".pdf"
    PNG = ".png"
    DOCX = ".docx"


@dataclass
class TestDocument:
    """Representa um documento de teste gerado"""
    path: Path
    format: DocumentFormat
    quality: DocumentQuality
    content_type: str          # "enunciado", "gabarito", "prova_aluno", "correcao"
    content: str               # Conteúdo do documento
    expected_extraction: Optional[Dict[str, Any]] = None
    expected_errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": str(self.path),
            "format": self.format.value,
            "quality": self.quality.value,
            "content_type": self.content_type,
            "has_content": bool(self.content),
            "expected_errors": self.expected_errors,
            "metadata": self.metadata
        }


# ============================================================
# DADOS PARA GERAÇÃO
# ============================================================

NOMES_ALUNOS = [
    "Ana Silva", "Bruno Santos", "Carla Oliveira", "Daniel Costa",
    "Elena Ferreira", "Felipe Rodrigues", "Gabriela Lima", "Hugo Almeida",
    "Isabela Martins", "João Pereira", "Kamila Souza", "Lucas Ribeiro",
    "Mariana Gomes", "Nicolas Barbosa", "Olivia Nascimento", "Pedro Carvalho"
]

QUESTOES_MATEMATICA = [
    {
        "enunciado": "Resolva a equação: 3x + 7 = 22",
        "resposta": "x = 5",
        "pontuacao": 2.0
    },
    {
        "enunciado": "Calcule a área de um triângulo com base 8cm e altura 5cm.",
        "resposta": "A = 20 cm²",
        "pontuacao": 2.0
    },
    {
        "enunciado": "Simplifique a expressão: 2(x + 3) - 4x",
        "resposta": "-2x + 6",
        "pontuacao": 2.0
    },
    {
        "enunciado": "Qual é o valor de 15% de 200?",
        "resposta": "30",
        "pontuacao": 2.0
    },
    {
        "enunciado": "Calcule: (2³ + 3²) × 2",
        "resposta": "34",
        "pontuacao": 2.0
    }
]

QUESTOES_PORTUGUES = [
    {
        "enunciado": "Identifique o sujeito da frase: 'Os alunos estudaram muito para a prova.'",
        "resposta": "Os alunos",
        "pontuacao": 2.0
    },
    {
        "enunciado": "Classifique quanto à transitividade: 'Ela dormiu cedo.'",
        "resposta": "Verbo intransitivo",
        "pontuacao": 2.0
    },
    {
        "enunciado": "Qual a classe gramatical de 'rapidamente'?",
        "resposta": "Advérbio de modo",
        "pontuacao": 2.0
    }
]

RESPOSTAS_QUALIDADE = {
    "excelente": {
        "acerto_chance": 0.95,
        "parcial_chance": 0.04,
        "erro_chance": 0.01
    },
    "bom": {
        "acerto_chance": 0.75,
        "parcial_chance": 0.15,
        "erro_chance": 0.10
    },
    "medio": {
        "acerto_chance": 0.50,
        "parcial_chance": 0.25,
        "erro_chance": 0.25
    },
    "ruim": {
        "acerto_chance": 0.20,
        "parcial_chance": 0.20,
        "erro_chance": 0.60
    }
}


class DocumentFactory:
    """
    Fábrica de documentos de teste para pipeline.

    Gera documentos em diferentes formatos e qualidades
    para testar robustez do sistema.
    """

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def criar_prova_teste(
        self,
        materia: str = "Matemática",
        num_questoes: int = 4,
        formato: DocumentFormat = DocumentFormat.TXT,
        qualidade: DocumentQuality = DocumentQuality.PERFECT
    ) -> TestDocument:
        """Cria documento de prova/enunciado para teste"""

        # Selecionar questões
        if materia.lower() == "matemática":
            questoes = random.sample(QUESTOES_MATEMATICA, min(num_questoes, len(QUESTOES_MATEMATICA)))
        else:
            questoes = random.sample(QUESTOES_PORTUGUES, min(num_questoes, len(QUESTOES_PORTUGUES)))

        # Gerar conteúdo
        data_prova = datetime.now().strftime("%d/%m/%Y")
        conteudo = f"""
ESCOLA MODELO - AVALIAÇÃO DE {materia.upper()}
Data: {data_prova}

Nome: _________________________________ Nº: _____

INSTRUÇÕES:
- Leia atentamente cada questão antes de responder
- Use caneta azul ou preta
- Boa prova!

═══════════════════════════════════════════════════════════════

"""
        for i, q in enumerate(questoes, 1):
            conteudo += f"QUESTÃO {i} ({q['pontuacao']:.1f} pontos)\n"
            conteudo += f"{q['enunciado']}\n\n"
            conteudo += "Resposta: ________________________________________________\n\n"

        conteudo += "═══════════════════════════════════════════════════════════════\n"

        # Aplicar qualidade
        if qualidade == DocumentQuality.POOR:
            conteudo = self._degradar_texto(conteudo)
        elif qualidade == DocumentQuality.CORRUPTED:
            conteudo = self._corromper_texto(conteudo)
        elif qualidade == DocumentQuality.EMPTY:
            conteudo = ""

        # Salvar arquivo
        filename = f"prova_{materia.lower()}_{uuid.uuid4().hex[:8]}{formato.value}"
        path = self.output_dir / filename
        path.write_text(conteudo, encoding="utf-8")

        # Expected extraction
        expected = {
            "total_questoes": num_questoes,
            "questoes": [
                {
                    "numero": i + 1,
                    "enunciado": q["enunciado"],
                    "pontuacao": q["pontuacao"]
                }
                for i, q in enumerate(questoes)
            ]
        }

        return TestDocument(
            path=path,
            format=formato,
            quality=qualidade,
            content_type="enunciado",
            content=conteudo,
            expected_extraction=expected,
            metadata={"materia": materia, "num_questoes": num_questoes}
        )

    def criar_gabarito_teste(
        self,
        materia: str = "Matemática",
        num_questoes: int = 4,
        formato: DocumentFormat = DocumentFormat.TXT
    ) -> TestDocument:
        """Cria gabarito para teste"""

        # Selecionar questões
        if materia.lower() == "matemática":
            questoes = random.sample(QUESTOES_MATEMATICA, min(num_questoes, len(QUESTOES_MATEMATICA)))
        else:
            questoes = random.sample(QUESTOES_PORTUGUES, min(num_questoes, len(QUESTOES_PORTUGUES)))

        conteudo = f"""
GABARITO - {materia.upper()}

"""
        for i, q in enumerate(questoes, 1):
            conteudo += f"Questão {i} ({q['pontuacao']:.1f} pts): {q['resposta']}\n"

        # Salvar
        filename = f"gabarito_{materia.lower()}_{uuid.uuid4().hex[:8]}{formato.value}"
        path = self.output_dir / filename
        path.write_text(conteudo, encoding="utf-8")

        expected = {
            "respostas": [
                {"numero": i + 1, "resposta": q["resposta"], "pontuacao": q["pontuacao"]}
                for i, q in enumerate(questoes)
            ]
        }

        return TestDocument(
            path=path,
            format=formato,
            quality=DocumentQuality.PERFECT,
            content_type="gabarito",
            content=conteudo,
            expected_extraction=expected,
            metadata={"materia": materia, "num_questoes": num_questoes}
        )

    def criar_prova_aluno(
        self,
        nome_aluno: str,
        materia: str = "Matemática",
        num_questoes: int = 4,
        qualidade_respostas: str = "medio",
        formato: DocumentFormat = DocumentFormat.TXT,
        problemas: Optional[List[str]] = None
    ) -> TestDocument:
        """
        Cria prova respondida de aluno.

        Args:
            nome_aluno: Nome do aluno
            materia: Matéria da prova
            num_questoes: Número de questões
            qualidade_respostas: "excelente", "bom", "medio", "ruim"
            formato: Formato do arquivo
            problemas: Lista de problemas a introduzir
                - "em_branco": Questões em branco
                - "ilegivel": Texto ilegível
                - "incompleto": Questões faltando
        """
        problemas = problemas or []

        # Selecionar questões
        if materia.lower() == "matemática":
            questoes = random.sample(QUESTOES_MATEMATICA, min(num_questoes, len(QUESTOES_MATEMATICA)))
        else:
            questoes = random.sample(QUESTOES_PORTUGUES, min(num_questoes, len(QUESTOES_PORTUGUES)))

        # Gerar respostas baseado na qualidade
        config = RESPOSTAS_QUALIDADE.get(qualidade_respostas, RESPOSTAS_QUALIDADE["medio"])

        data_prova = datetime.now().strftime("%d/%m/%Y")
        conteudo = f"""
ESCOLA MODELO - AVALIAÇÃO DE {materia.upper()}
Data: {data_prova}

Nome: {nome_aluno}                               Nº: {random.randint(1, 40)}

═══════════════════════════════════════════════════════════════

"""
        respostas_geradas = []
        for i, q in enumerate(questoes, 1):
            conteudo += f"QUESTÃO {i} ({q['pontuacao']:.1f} pontos)\n"
            conteudo += f"{q['enunciado']}\n\n"

            # Gerar resposta baseado na qualidade
            rand = random.random()
            if "em_branco" in problemas and random.random() < 0.3:
                resposta = ""
                status = "em_branco"
            elif rand < config["acerto_chance"]:
                resposta = q["resposta"]
                status = "correta"
            elif rand < config["acerto_chance"] + config["parcial_chance"]:
                resposta = self._gerar_resposta_parcial(q["resposta"])
                status = "parcial"
            else:
                resposta = self._gerar_resposta_errada(q["resposta"])
                status = "errada"

            if "ilegivel" in problemas and random.random() < 0.2:
                resposta = self._tornar_ilegivel(resposta)
                status = "ilegivel"

            conteudo += f"Resposta: {resposta}\n\n"
            respostas_geradas.append({
                "numero": i,
                "resposta": resposta,
                "status": status
            })

        # Aplicar problema de incompletude
        if "incompleto" in problemas:
            conteudo = conteudo[:int(len(conteudo) * 0.7)]
            conteudo += "\n[DOCUMENTO INCOMPLETO]"

        # Salvar
        filename = f"prova_aluno_{nome_aluno.replace(' ', '_')}_{uuid.uuid4().hex[:8]}{formato.value}"
        path = self.output_dir / filename
        path.write_text(conteudo, encoding="utf-8")

        return TestDocument(
            path=path,
            format=formato,
            quality=DocumentQuality.NORMAL if not problemas else DocumentQuality.POOR,
            content_type="prova_aluno",
            content=conteudo,
            expected_extraction={"respostas": respostas_geradas},
            expected_errors=problemas,
            metadata={
                "aluno": nome_aluno,
                "materia": materia,
                "qualidade": qualidade_respostas
            }
        )

    def criar_documento_corrompido(
        self,
        tipo_corrupcao: str = "json_invalido"
    ) -> TestDocument:
        """
        Cria documento propositalmente corrompido.

        Tipos de corrupção:
        - "json_invalido": JSON malformado
        - "texto_aleatorio": Texto sem sentido
        - "arquivo_vazio": Arquivo de 0 bytes
        - "encoding_errado": Texto com encoding quebrado
        - "truncado": Documento cortado no meio
        """
        filename = f"corrupted_{tipo_corrupcao}_{uuid.uuid4().hex[:8]}.txt"
        path = self.output_dir / filename

        if tipo_corrupcao == "json_invalido":
            conteudo = '{"questoes": [{"numero": 1, "resposta": "incompleto...'
        elif tipo_corrupcao == "texto_aleatorio":
            conteudo = "".join(random.choices("abcdefghijklmnopqrstuvwxyz0123456789!@#$%", k=500))
        elif tipo_corrupcao == "arquivo_vazio":
            conteudo = ""
        elif tipo_corrupcao == "encoding_errado":
            conteudo = "Questão com acentuação: ção ão é à"
            # Escrever com encoding errado
            path.write_bytes(conteudo.encode("latin-1"))
            return TestDocument(
                path=path,
                format=DocumentFormat.TXT,
                quality=DocumentQuality.CORRUPTED,
                content_type="corrupted",
                content=conteudo,
                expected_errors=[tipo_corrupcao],
                metadata={"tipo_corrupcao": tipo_corrupcao}
            )
        elif tipo_corrupcao == "truncado":
            conteudo = """PROVA DE MATEMÁTICA
Questão 1: Resolva 2+2
Resposta: 4

Questão 2: Calcule a área de"""  # Cortado
        else:
            conteudo = f"Tipo de corrupção desconhecido: {tipo_corrupcao}"

        path.write_text(conteudo, encoding="utf-8")

        return TestDocument(
            path=path,
            format=DocumentFormat.TXT,
            quality=DocumentQuality.CORRUPTED,
            content_type="corrupted",
            content=conteudo,
            expected_errors=[tipo_corrupcao],
            metadata={"tipo_corrupcao": tipo_corrupcao}
        )

    def criar_cenario_completo(
        self,
        materia: str = "Matemática",
        num_alunos: int = 2,
        num_questoes: int = 4,
        qualidades: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Cria cenário completo para teste de pipeline.

        Returns:
            {
                "materia": "Matemática",
                "materia_id": "uuid",
                "turma_id": "uuid",
                "atividade_id": "uuid",
                "enunciado": TestDocument,
                "gabarito": TestDocument,
                "alunos": [
                    {"aluno_id": "uuid", "nome": "Ana", "prova": TestDocument},
                    ...
                ]
            }
        """
        qualidades = qualidades or ["excelente", "medio"]

        # IDs fictícios
        materia_id = str(uuid.uuid4())
        turma_id = str(uuid.uuid4())
        atividade_id = str(uuid.uuid4())

        # Criar documentos base
        enunciado = self.criar_prova_teste(materia, num_questoes)
        gabarito = self.criar_gabarito_teste(materia, num_questoes)

        # Criar provas dos alunos
        alunos = []
        nomes_selecionados = random.sample(NOMES_ALUNOS, min(num_alunos, len(NOMES_ALUNOS)))

        for i, nome in enumerate(nomes_selecionados):
            qualidade = qualidades[i % len(qualidades)]
            prova = self.criar_prova_aluno(
                nome_aluno=nome,
                materia=materia,
                num_questoes=num_questoes,
                qualidade_respostas=qualidade
            )
            alunos.append({
                "aluno_id": str(uuid.uuid4()),
                "nome": nome,
                "qualidade": qualidade,
                "prova": prova
            })

        return {
            "materia": materia,
            "materia_id": materia_id,
            "turma_id": turma_id,
            "atividade_id": atividade_id,
            "enunciado": enunciado,
            "gabarito": gabarito,
            "alunos": alunos,
            "num_questoes": num_questoes
        }

    # ============================================================
    # MÉTODOS AUXILIARES
    # ============================================================

    def _degradar_texto(self, texto: str) -> str:
        """Degrada qualidade do texto (simula OCR ruim)"""
        replacements = {
            "a": ["@", "4"],
            "e": ["3", "€"],
            "o": ["0", "°"],
            "i": ["1", "!"],
            "s": ["$", "5"]
        }
        resultado = texto
        for char, alternatives in replacements.items():
            if random.random() < 0.1:
                resultado = resultado.replace(char, random.choice(alternatives), 1)
        return resultado

    def _corromper_texto(self, texto: str) -> str:
        """Corrompe texto severamente"""
        chars = list(texto)
        for i in range(len(chars)):
            if random.random() < 0.15:
                chars[i] = random.choice("░▒▓█▄▀■□●○")
        return "".join(chars)

    def _gerar_resposta_parcial(self, resposta_correta: str) -> str:
        """Gera resposta parcialmente correta"""
        # Simplificar ou truncar
        if len(resposta_correta) > 5:
            return resposta_correta[:len(resposta_correta) // 2] + "..."
        return resposta_correta.replace("=", "≈")

    def _gerar_resposta_errada(self, resposta_correta: str) -> str:
        """Gera resposta incorreta"""
        erros_comuns = [
            "Não sei",
            "???",
            str(random.randint(1, 100)),
            "A resposta é diferente",
            ""
        ]
        return random.choice(erros_comuns)

    def _tornar_ilegivel(self, texto: str) -> str:
        """Torna texto ilegível"""
        return "".join(
            c if random.random() > 0.4 else random.choice("?░▒")
            for c in texto
        )

    def limpar(self):
        """Remove todos os arquivos gerados"""
        import shutil
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
