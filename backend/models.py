"""
PROVA AI - Modelos de Dados v2.0

Estrutura hierárquica:
    Matéria → Turma → Atividade → Aluno/Documentos

Este arquivo define todos os modelos de dados usados no sistema.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import json


# ============================================================
# ENUMS - Tipos e Categorias
# ============================================================

def _normalize_metadata(raw_metadata: Any) -> Dict[str, Any]:
    if raw_metadata is None:
        return {}
    if isinstance(raw_metadata, dict):
        return raw_metadata
    if isinstance(raw_metadata, str):
        try:
            parsed = json.loads(raw_metadata)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}

class TipoDocumento(Enum):
    """
    Tipos de documento no sistema.
    Divididos em 3 categorias:
    - BASE: Documentos da atividade (professor faz upload)
    - ALUNO: Documentos do aluno (professor faz upload)
    - GERADO: Documentos gerados pela IA
    """
    
    # === DOCUMENTOS BASE (nível Atividade) ===
    ENUNCIADO = "enunciado"                    # Prova/atividade em branco
    GABARITO = "gabarito"                      # Respostas corretas
    CRITERIOS_CORRECAO = "criterios_correcao"  # Rubrica/critérios de avaliação
    MATERIAL_APOIO = "material_apoio"          # Material extra (opcional)
    
    # === DOCUMENTOS DO ALUNO (nível Aluno) ===
    PROVA_RESPONDIDA = "prova_respondida"      # Prova feita pelo aluno
    CORRECAO_PROFESSOR = "correcao_professor"  # Correção feita pelo professor
    
    # === DOCUMENTOS GERADOS PELA IA (nível Aluno) ===
    EXTRACAO_QUESTOES = "extracao_questoes"    # Questões extraídas do enunciado
    EXTRACAO_GABARITO = "extracao_gabarito"    # Respostas extraídas do gabarito
    EXTRACAO_RESPOSTAS = "extracao_respostas"  # Respostas extraídas do aluno
    CORRECAO = "correcao"                      # Correção questão por questão
    ANALISE_HABILIDADES = "analise_habilidades"# Análise de competências
    RELATORIO_FINAL = "relatorio_final"        # Relatório para o professor
    
    @classmethod
    def documentos_base(cls) -> List['TipoDocumento']:
        """Retorna tipos que são documentos base da atividade"""
        return [cls.ENUNCIADO, cls.GABARITO, cls.CRITERIOS_CORRECAO, cls.MATERIAL_APOIO]

    @classmethod
    def documentos_atividade_gerados(cls) -> List['TipoDocumento']:
        """Retorna tipos gerados pela IA que são nível atividade (não precisam de aluno_id)"""
        return [cls.EXTRACAO_QUESTOES, cls.EXTRACAO_GABARITO]

    @classmethod
    def documentos_sem_aluno(cls) -> List['TipoDocumento']:
        """Retorna todos os tipos que NÃO precisam de aluno_id"""
        return cls.documentos_base() + cls.documentos_atividade_gerados()
    
    @classmethod
    def documentos_aluno(cls) -> List['TipoDocumento']:
        """Retorna tipos que são uploads do aluno"""
        return [cls.PROVA_RESPONDIDA, cls.CORRECAO_PROFESSOR]
    
    @classmethod
    def documentos_gerados(cls) -> List['TipoDocumento']:
        """Retorna tipos gerados pela IA"""
        return [
            cls.EXTRACAO_QUESTOES, cls.EXTRACAO_GABARITO, cls.EXTRACAO_RESPOSTAS,
            cls.CORRECAO, cls.ANALISE_HABILIDADES, cls.RELATORIO_FINAL
        ]


class StatusProcessamento(Enum):
    """Status de um documento gerado"""
    PENDENTE = "pendente"        # Ainda não processado
    PROCESSANDO = "processando"  # Em andamento
    CONCLUIDO = "concluido"      # Finalizado com sucesso
    ERRO = "erro"                # Falhou


# ============================================================
# FRAMEWORK DE ERROS DO PIPELINE
# ============================================================

# Constantes de tipo de erro (extensível — adicionar novas strings para novos tipos)
ERRO_DOCUMENTO_FALTANTE = "DOCUMENTO_FALTANTE"
ERRO_QUESTOES_FALTANTES = "QUESTOES_FALTANTES"


class SeveridadeErro(Enum):
    """Severidade de um erro no pipeline."""
    CRITICO = "critico"
    ALTO = "alto"
    MEDIO = "medio"


def criar_erro_pipeline(tipo: str, mensagem: str, severidade, etapa: str) -> dict:
    """Cria um dict estruturado de erro para incluir nos JSONs do pipeline.

    Args:
        tipo: Tipo de erro (ex: ERRO_DOCUMENTO_FALTANTE)
        mensagem: Descrição humana do erro
        severidade: SeveridadeErro enum ou string
        etapa: Nome da etapa que gerou o erro

    Returns:
        Dict com tipo, mensagem, severidade, etapa, timestamp
    """
    sev_value = severidade.value if isinstance(severidade, SeveridadeErro) else str(severidade)
    return {
        "tipo": tipo,
        "mensagem": mensagem,
        "severidade": sev_value,
        "etapa": etapa,
        "timestamp": datetime.now().isoformat()
    }


class NivelEnsino(Enum):
    """Níveis de ensino (opcional, para organização)"""
    FUNDAMENTAL_1 = "fundamental_1"
    FUNDAMENTAL_2 = "fundamental_2"
    MEDIO = "medio"
    SUPERIOR = "superior"
    OUTRO = "outro"


# ============================================================
# MODELOS PRINCIPAIS
# ============================================================

@dataclass
class Materia:
    """
    Representa uma matéria/disciplina.
    Ex: Matemática, Português, Física
    """
    id: str
    nome: str
    descricao: Optional[str] = None
    nivel: NivelEnsino = NivelEnsino.OUTRO
    criado_em: datetime = field(default_factory=datetime.now)
    atualizado_em: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nome": self.nome,
            "descricao": self.descricao,
            "nivel": self.nivel.value,
            "criado_em": self.criado_em.isoformat(),
            "atualizado_em": self.atualizado_em.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Materia':
        return cls(
            id=data["id"],
            nome=data["nome"],
            descricao=data.get("descricao"),
            nivel=NivelEnsino(data.get("nivel", "outro")),
            criado_em=datetime.fromisoformat(data["criado_em"]) if "criado_em" in data else datetime.now(),
            atualizado_em=datetime.fromisoformat(data["atualizado_em"]) if "atualizado_em" in data else datetime.now(),
            metadata=_normalize_metadata(data.get("metadata"))
        )


@dataclass
class Turma:
    """
    Representa uma turma dentro de uma matéria.
    Ex: "9º Ano A - 2024", "Turma de Sábado"
    
    Uma turma pertence a UMA matéria.
    """
    id: str
    materia_id: str              # FK para Materia
    nome: str                    # Ex: "9º Ano A"
    ano_letivo: Optional[int] = None  # Ex: 2024
    periodo: Optional[str] = None     # Ex: "1º Semestre", "Manhã"
    descricao: Optional[str] = None
    criado_em: datetime = field(default_factory=datetime.now)
    atualizado_em: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "materia_id": self.materia_id,
            "nome": self.nome,
            "ano_letivo": self.ano_letivo,
            "periodo": self.periodo,
            "descricao": self.descricao,
            "criado_em": self.criado_em.isoformat(),
            "atualizado_em": self.atualizado_em.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Turma':
        return cls(
            id=data["id"],
            materia_id=data["materia_id"],
            nome=data["nome"],
            ano_letivo=data.get("ano_letivo"),
            periodo=data.get("periodo"),
            descricao=data.get("descricao"),
            criado_em=datetime.fromisoformat(data["criado_em"]) if "criado_em" in data else datetime.now(),
            atualizado_em=datetime.fromisoformat(data["atualizado_em"]) if "atualizado_em" in data else datetime.now(),
            metadata=_normalize_metadata(data.get("metadata"))
        )


@dataclass
class Aluno:
    """
    Representa um aluno.
    
    Um aluno pode estar em MÚLTIPLAS turmas (inclusive repetindo matéria).
    A vinculação aluno-turma é feita pela tabela AlunoTurma.
    """
    id: str
    nome: str
    email: Optional[str] = None
    matricula: Optional[str] = None  # Número de matrícula
    criado_em: datetime = field(default_factory=datetime.now)
    atualizado_em: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nome": self.nome,
            "email": self.email,
            "matricula": self.matricula,
            "criado_em": self.criado_em.isoformat(),
            "atualizado_em": self.atualizado_em.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Aluno':
        return cls(
            id=data["id"],
            nome=data["nome"],
            email=data.get("email"),
            matricula=data.get("matricula"),
            criado_em=datetime.fromisoformat(data["criado_em"]) if "criado_em" in data else datetime.now(),
            atualizado_em=datetime.fromisoformat(data["atualizado_em"]) if "atualizado_em" in data else datetime.now(),
            metadata=_normalize_metadata(data.get("metadata"))
        )


@dataclass
class AlunoTurma:
    """
    Vinculação entre Aluno e Turma (many-to-many).
    Permite que um aluno esteja em múltiplas turmas.
    """
    id: str
    aluno_id: str
    turma_id: str
    ativo: bool = True           # Se o aluno ainda está na turma
    data_entrada: datetime = field(default_factory=datetime.now)
    data_saida: Optional[datetime] = None
    observacoes: Optional[str] = None  # Ex: "Repetente", "Transferido"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "aluno_id": self.aluno_id,
            "turma_id": self.turma_id,
            "ativo": self.ativo,
            "data_entrada": self.data_entrada.isoformat(),
            "data_saida": self.data_saida.isoformat() if self.data_saida else None,
            "observacoes": self.observacoes
        }


@dataclass
class Atividade:
    """
    Representa uma atividade/prova dentro de uma turma.
    Ex: "Prova 1 - Bimestre 1", "Trabalho de Recuperação"
    
    Uma atividade pertence a UMA turma.
    """
    id: str
    turma_id: str                # FK para Turma
    nome: str                    # Ex: "Prova 1"
    tipo: Optional[str] = None   # Ex: "prova", "trabalho", "exercicio"
    data_aplicacao: Optional[datetime] = None  # Quando foi/será aplicada
    data_entrega: Optional[datetime] = None    # Prazo de entrega
    peso: float = 1.0            # Peso na média
    nota_maxima: float = 10.0    # Nota máxima possível
    descricao: Optional[str] = None
    criado_em: datetime = field(default_factory=datetime.now)
    atualizado_em: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "turma_id": self.turma_id,
            "nome": self.nome,
            "tipo": self.tipo,
            "data_aplicacao": self.data_aplicacao.isoformat() if self.data_aplicacao else None,
            "data_entrega": self.data_entrega.isoformat() if self.data_entrega else None,
            "peso": self.peso,
            "nota_maxima": self.nota_maxima,
            "descricao": self.descricao,
            "criado_em": self.criado_em.isoformat(),
            "atualizado_em": self.atualizado_em.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Atividade':
        return cls(
            id=data["id"],
            turma_id=data["turma_id"],
            nome=data["nome"],
            tipo=data.get("tipo"),
            data_aplicacao=datetime.fromisoformat(data["data_aplicacao"]) if data.get("data_aplicacao") else None,
            data_entrega=datetime.fromisoformat(data["data_entrega"]) if data.get("data_entrega") else None,
            peso=data.get("peso", 1.0),
            nota_maxima=data.get("nota_maxima", 10.0),
            descricao=data.get("descricao"),
            criado_em=datetime.fromisoformat(data["criado_em"]) if "criado_em" in data else datetime.now(),
            atualizado_em=datetime.fromisoformat(data["atualizado_em"]) if "atualizado_em" in data else datetime.now(),
            metadata=_normalize_metadata(data.get("metadata"))
        )


@dataclass
class Documento:
    """
    Representa qualquer documento no sistema.
    
    Pode ser:
    - Documento base da atividade (enunciado, gabarito, critérios)
    - Documento do aluno (prova respondida)
    - Documento gerado pela IA (correção, relatório)
    
    O campo 'nivel' indica onde o documento está na hierarquia:
    - nivel='atividade': documento base (sem aluno_id)
    - nivel='aluno': documento do aluno ou gerado (com aluno_id)
    """
    id: str
    tipo: TipoDocumento
    atividade_id: str            # FK para Atividade (sempre obrigatório)
    aluno_id: Optional[str] = None  # FK para Aluno (só para docs de aluno/gerados)
    
    # Arquivo
    nome_arquivo: str = ""       # Nome original do arquivo
    caminho_arquivo: str = ""    # Caminho no sistema de arquivos
    extensao: str = ""           # Ex: ".pdf", ".docx"
    tamanho_bytes: int = 0
    
    # Metadados de processamento (para docs gerados)
    ia_provider: Optional[str] = None     # Ex: "openai-gpt4o"
    ia_modelo: Optional[str] = None       # Ex: "gpt-4o"
    prompt_usado: Optional[str] = None    # ID ou texto do prompt
    prompt_versao: Optional[str] = None   # Versão do prompt
    tokens_usados: int = 0
    tempo_processamento_ms: float = 0
    status: StatusProcessamento = StatusProcessamento.CONCLUIDO
    
    # Controle
    criado_em: datetime = field(default_factory=datetime.now)
    atualizado_em: datetime = field(default_factory=datetime.now)
    criado_por: Optional[str] = None      # Usuário ou "sistema"
    versao: int = 1                       # Para histórico de versões
    documento_origem_id: Optional[str] = None  # Se foi re-processado, qual era o original
    
    # Dados extras
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tipo": self.tipo.value,
            "atividade_id": self.atividade_id,
            "aluno_id": self.aluno_id,
            "nome_arquivo": self.nome_arquivo,
            "caminho_arquivo": self.caminho_arquivo,
            "extensao": self.extensao,
            "tamanho_bytes": self.tamanho_bytes,
            "ia_provider": self.ia_provider,
            "ia_modelo": self.ia_modelo,
            "prompt_usado": self.prompt_usado,
            "prompt_versao": self.prompt_versao,
            "tokens_usados": self.tokens_usados,
            "tempo_processamento_ms": self.tempo_processamento_ms,
            "status": self.status.value,
            "criado_em": self.criado_em.isoformat(),
            "atualizado_em": self.atualizado_em.isoformat(),
            "criado_por": self.criado_por,
            "versao": self.versao,
            "documento_origem_id": self.documento_origem_id,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Documento':
        return cls(
            id=data["id"],
            tipo=TipoDocumento(data["tipo"]),
            atividade_id=data["atividade_id"],
            aluno_id=data.get("aluno_id"),
            nome_arquivo=data.get("nome_arquivo", ""),
            caminho_arquivo=data.get("caminho_arquivo", ""),
            extensao=data.get("extensao", ""),
            tamanho_bytes=data.get("tamanho_bytes", 0),
            ia_provider=data.get("ia_provider"),
            ia_modelo=data.get("ia_modelo"),
            prompt_usado=data.get("prompt_usado"),
            prompt_versao=data.get("prompt_versao"),
            tokens_usados=data.get("tokens_usados", 0),
            tempo_processamento_ms=data.get("tempo_processamento_ms", 0),
            status=StatusProcessamento(data.get("status", "concluido")),
            criado_em=datetime.fromisoformat(data["criado_em"]) if "criado_em" in data else datetime.now(),
            atualizado_em=datetime.fromisoformat(data["atualizado_em"]) if "atualizado_em" in data else datetime.now(),
            criado_por=data.get("criado_por"),
            versao=data.get("versao", 1),
            documento_origem_id=data.get("documento_origem_id"),
            metadata=_normalize_metadata(data.get("metadata"))
        )
    
    @property
    def is_documento_base(self) -> bool:
        """Verifica se é um documento base da atividade"""
        return self.tipo in TipoDocumento.documentos_base()
    
    @property
    def is_documento_aluno(self) -> bool:
        """Verifica se é um documento enviado pelo/do aluno"""
        return self.tipo in TipoDocumento.documentos_aluno()
    
    @property
    def is_documento_gerado(self) -> bool:
        """Verifica se é um documento gerado pela IA"""
        return self.tipo in TipoDocumento.documentos_gerados()


# ============================================================
# MODELOS DE SUPORTE
# ============================================================

@dataclass
class Prompt:
    """
    Representa um prompt reutilizável para processamento.
    Pode ser padrão do sistema ou customizado pelo usuário.
    """
    id: str
    nome: str                    # Ex: "Extração de Questões - Padrão"
    etapa: str                   # Ex: "extracao_questoes", "correcao"
    texto: str                   # O prompt em si
    descricao: Optional[str] = None
    is_padrao: bool = True       # Se é o prompt padrão do sistema
    materia_id: Optional[str] = None  # Se é específico para uma matéria
    criado_em: datetime = field(default_factory=datetime.now)
    atualizado_em: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nome": self.nome,
            "etapa": self.etapa,
            "texto": self.texto,
            "descricao": self.descricao,
            "is_padrao": self.is_padrao,
            "materia_id": self.materia_id,
            "criado_em": self.criado_em.isoformat(),
            "atualizado_em": self.atualizado_em.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class ResultadoAluno:
    """
    Representa o resultado consolidado de um aluno em uma atividade.
    Agregação dos dados de correção para fácil consulta.
    """
    id: str
    aluno_id: str
    atividade_id: str
    
    nota_obtida: Optional[float] = None
    nota_maxima: float = 10.0
    percentual: Optional[float] = None
    
    total_questoes: int = 0
    questoes_corretas: int = 0
    questoes_parciais: int = 0
    questoes_incorretas: int = 0
    
    habilidades_demonstradas: List[str] = field(default_factory=list)
    habilidades_faltantes: List[str] = field(default_factory=list)
    
    feedback_geral: Optional[str] = None
    
    corrigido_em: Optional[datetime] = None
    corrigido_por_ia: Optional[str] = None
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "aluno_id": self.aluno_id,
            "atividade_id": self.atividade_id,
            "nota_obtida": self.nota_obtida,
            "nota_maxima": self.nota_maxima,
            "percentual": self.percentual,
            "total_questoes": self.total_questoes,
            "questoes_corretas": self.questoes_corretas,
            "questoes_parciais": self.questoes_parciais,
            "questoes_incorretas": self.questoes_incorretas,
            "habilidades_demonstradas": self.habilidades_demonstradas,
            "habilidades_faltantes": self.habilidades_faltantes,
            "feedback_geral": self.feedback_geral,
            "corrigido_em": self.corrigido_em.isoformat() if self.corrigido_em else None,
            "corrigido_por_ia": self.corrigido_por_ia,
            "metadata": self.metadata
        }


# ============================================================
# DEPENDÊNCIAS DE DOCUMENTOS
# ============================================================

# Define quais documentos são necessários para cada tipo de processamento
DEPENDENCIAS_DOCUMENTOS = {
    # Para extrair questões, precisa do enunciado
    TipoDocumento.EXTRACAO_QUESTOES: {
        "obrigatorios": [TipoDocumento.ENUNCIADO],
        "opcionais": []
    },
    
    # Para extrair gabarito, precisa do gabarito
    TipoDocumento.EXTRACAO_GABARITO: {
        "obrigatorios": [TipoDocumento.GABARITO],
        "opcionais": [TipoDocumento.ENUNCIADO]
    },
    
    # Para extrair respostas do aluno, precisa da prova respondida
    TipoDocumento.EXTRACAO_RESPOSTAS: {
        "obrigatorios": [TipoDocumento.PROVA_RESPONDIDA],
        "opcionais": [TipoDocumento.ENUNCIADO, TipoDocumento.EXTRACAO_QUESTOES]
    },
    
    # Para corrigir, precisa das respostas do aluno e do gabarito
    TipoDocumento.CORRECAO: {
        "obrigatorios": [TipoDocumento.EXTRACAO_RESPOSTAS, TipoDocumento.GABARITO],
        "opcionais": [TipoDocumento.CRITERIOS_CORRECAO, TipoDocumento.EXTRACAO_GABARITO]
    },
    
    # Para analisar habilidades, precisa da correção
    TipoDocumento.ANALISE_HABILIDADES: {
        "obrigatorios": [TipoDocumento.CORRECAO],
        "opcionais": [TipoDocumento.CRITERIOS_CORRECAO]
    },
    
    # Para gerar relatório, precisa de tudo
    TipoDocumento.RELATORIO_FINAL: {
        "obrigatorios": [TipoDocumento.CORRECAO],
        "opcionais": [TipoDocumento.ANALISE_HABILIDADES, TipoDocumento.CRITERIOS_CORRECAO]
    }
}


def verificar_dependencias(tipo_alvo: TipoDocumento, documentos_existentes: List[TipoDocumento]) -> Dict[str, Any]:
    """
    Verifica se os documentos necessários existem para processar um tipo.
    
    Retorna:
        {
            "pode_processar": bool,
            "faltando_obrigatorios": List[TipoDocumento],
            "faltando_opcionais": List[TipoDocumento],
            "aviso": str ou None
        }
    """
    if tipo_alvo not in DEPENDENCIAS_DOCUMENTOS:
        return {
            "pode_processar": True,
            "faltando_obrigatorios": [],
            "faltando_opcionais": [],
            "aviso": None
        }
    
    deps = DEPENDENCIAS_DOCUMENTOS[tipo_alvo]
    
    faltando_obrig = [d for d in deps["obrigatorios"] if d not in documentos_existentes]
    faltando_opc = [d for d in deps["opcionais"] if d not in documentos_existentes]
    
    pode_processar = len(faltando_obrig) == 0
    
    aviso = None
    if faltando_opc:
        nomes = [d.value for d in faltando_opc]
        aviso = f"Documentos opcionais faltando: {', '.join(nomes)}. O resultado pode ser menos preciso."
    
    return {
        "pode_processar": pode_processar,
        "faltando_obrigatorios": faltando_obrig,
        "faltando_opcionais": faltando_opc,
        "aviso": aviso
    }
