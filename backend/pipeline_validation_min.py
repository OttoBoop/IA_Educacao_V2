"""
NOVO CR - Validation Models for Pipeline JSON Outputs v2.0
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class TipoQuestao(str, Enum):
    MULTIPLA_ESCOLHA = "multipla_escolha"
    DISSERTATIVA = "dissertativa"


class ItemQuestao(BaseModel):
    letra: str
    texto: str


class Questao(BaseModel):
    numero: int
    enunciado: str
    itens: List[ItemQuestao] = []
    tipo: TipoQuestao
    pontuacao: float
    habilidades: List[str] = []


class ExtracaoQuestoes(BaseModel):
    questoes: List[Questao]
    total_questoes: int
    pontuacao_total: float


def obter_schema_json(etapa: str):
    modelos = {
        'extrair_questoes': ExtracaoQuestoes,
    }
    modelo = modelos.get(etapa.lower().replace(' ', '_'))
    if modelo:
        return modelo.schema()
    else:
        return None


# Test
if __name__ == "__main__":
    print("Testing...")
    schema = obter_schema_json("extrair_questoes")
    print("Schema obtained:", schema is not None)</content>
<parameter name="filePath">c:\Users\otavi\Documents\prova-ai\IA_Educacao_V2\backend\pipeline_validation_min.py