"""
PROVA AI - Sistema de Prompts v2.0

Gerencia prompts reutilizáveis para cada etapa do pipeline.
Permite criar, editar e versionar prompts.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import json
import sqlite3
from pathlib import Path


class EtapaProcessamento(Enum):
    """Etapas do pipeline de correção"""
    EXTRAIR_QUESTOES = "extrair_questoes"
    EXTRAIR_GABARITO = "extrair_gabarito"
    EXTRAIR_RESPOSTAS = "extrair_respostas"
    CORRIGIR = "corrigir"
    ANALISAR_HABILIDADES = "analisar_habilidades"
    GERAR_RELATORIO = "gerar_relatorio"
    CHAT_GERAL = "chat_geral"


@dataclass
class PromptTemplate:
    """Um template de prompt reutilizável"""
    id: str
    nome: str
    etapa: EtapaProcessamento
    texto: str
    texto_sistema: Optional[str] = None
    descricao: Optional[str] = None
    
    # Configurações
    is_padrao: bool = False          # Se é o prompt padrão da etapa
    is_ativo: bool = True            # Se está disponível para uso
    
    # Escopo
    materia_id: Optional[str] = None  # None = global
    
    # Variáveis esperadas no prompt (para validação)
    variaveis: List[str] = field(default_factory=list)
    
    # Metadados
    versao: int = 1
    criado_em: datetime = field(default_factory=datetime.now)
    atualizado_em: datetime = field(default_factory=datetime.now)
    criado_por: str = "sistema"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "nome": self.nome,
            "etapa": self.etapa.value,
            "texto": self.texto,
            "texto_sistema": self.texto_sistema,
            "descricao": self.descricao,
            "is_padrao": self.is_padrao,
            "is_ativo": self.is_ativo,
            "materia_id": self.materia_id,
            "variaveis": self.variaveis,
            "versao": self.versao,
            "criado_em": self.criado_em.isoformat(),
            "atualizado_em": self.atualizado_em.isoformat(),
            "criado_por": self.criado_por
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptTemplate':
        return cls(
            id=data["id"],
            nome=data["nome"],
            etapa=EtapaProcessamento(data["etapa"]),
            texto=data["texto"],
            texto_sistema=data.get("texto_sistema"),
            descricao=data.get("descricao"),
            is_padrao=data.get("is_padrao", False),
            is_ativo=data.get("is_ativo", True),
            materia_id=data.get("materia_id"),
            variaveis=data.get("variaveis", []),
            versao=data.get("versao", 1),
            criado_em=datetime.fromisoformat(data["criado_em"]) if "criado_em" in data else datetime.now(),
            atualizado_em=datetime.fromisoformat(data["atualizado_em"]) if "atualizado_em" in data else datetime.now(),
            criado_por=data.get("criado_por", "sistema")
        )
    
    def render(self, **kwargs) -> str:
        """Renderiza o prompt do usuário substituindo variáveis"""
        return self._render_texto(self.texto, **kwargs)

    def render_sistema(self, **kwargs) -> str:
        """Renderiza o prompt de sistema substituindo variáveis"""
        if not self.texto_sistema:
            return ""
        return self._render_texto(self.texto_sistema, **kwargs)

    @staticmethod
    def _render_texto(texto: str, **kwargs) -> str:
        """Renderiza um texto substituindo variáveis"""
        for var, valor in kwargs.items():
            texto = texto.replace(f"{{{{{var}}}}}", str(valor))
        return texto


# ============================================================
# PROMPTS PADRÃO DO SISTEMA
# ============================================================

PROMPTS_PADRAO = {
    EtapaProcessamento.EXTRAIR_QUESTOES: PromptTemplate(
        id="default_extrair_questoes",
        nome="Extração de Questões - Padrão",
        etapa=EtapaProcessamento.EXTRAIR_QUESTOES,
        descricao="Extrai questões de um enunciado de prova",
        is_padrao=True,
        variaveis=["conteudo_documento", "materia"],
        texto="""Você é um assistente especializado em análise de provas educacionais.

Analise o documento a seguir e extraia TODAS as questões encontradas.

**Matéria:** {{materia}}

**Documento:**
{{conteudo_documento}}

Para cada questão, retorne um JSON no seguinte formato:
```json
{
  "questoes": [
    {
      "numero": 1,
      "enunciado": "Texto completo do enunciado",
      "itens": [
        {"letra": "a", "texto": "Texto do item a"},
        {"letra": "b", "texto": "Texto do item b"}
      ],
      "tipo": "multipla_escolha|dissertativa|verdadeiro_falso|associacao",
      "pontuacao": 1.0,
      "habilidades": ["habilidade1", "habilidade2"]
    }
  ],
  "total_questoes": 10,
  "pontuacao_total": 10.0
}
```

Seja preciso e extraia exatamente o que está no documento."""
    ),
    
    EtapaProcessamento.EXTRAIR_GABARITO: PromptTemplate(
        id="default_extrair_gabarito",
        nome="Extração de Gabarito - Padrão",
        etapa=EtapaProcessamento.EXTRAIR_GABARITO,
        descricao="Extrai respostas corretas do gabarito",
        is_padrao=True,
        variaveis=["conteudo_documento", "questoes_extraidas"],
        texto="""Você é um assistente especializado em análise de gabaritos.

Analise o gabarito a seguir e extraia as respostas corretas para cada questão.

**Questões já identificadas:**
{{questoes_extraidas}}

**Gabarito:**
{{conteudo_documento}}

Para cada questão, retorne um JSON:
```json
{
  "respostas": [
    {
      "questao_numero": 1,
      "resposta_correta": "a",
      "justificativa": "Explicação de por que esta é a resposta correta (se disponível)",
      "criterios_parciais": [
        {"descricao": "Critério para nota parcial", "percentual": 50}
      ]
    }
  ]
}
```

Se houver critérios de correção detalhados, inclua-os."""
    ),
    
    EtapaProcessamento.EXTRAIR_RESPOSTAS: PromptTemplate(
        id="default_extrair_respostas",
        nome="Extração de Respostas do Aluno - Padrão",
        etapa=EtapaProcessamento.EXTRAIR_RESPOSTAS,
        descricao="Extrai respostas da prova do aluno",
        is_padrao=True,
        variaveis=["conteudo_documento", "questoes_extraidas", "nome_aluno"],
        texto="""Você é um assistente especializado em leitura de provas respondidas.

Analise a prova respondida pelo aluno e extraia suas respostas.

**Aluno:** {{nome_aluno}}

**Questões da prova:**
{{questoes_extraidas}}

**Prova respondida:**
{{conteudo_documento}}

Para cada questão, retorne um JSON:
```json
{
  "aluno": "{{nome_aluno}}",
  "respostas": [
    {
      "questao_numero": 1,
      "resposta_aluno": "Resposta dada pelo aluno",
      "em_branco": false,
      "ilegivel": false,
      "observacoes": "Qualquer observação relevante"
    }
  ],
  "questoes_respondidas": 8,
  "questoes_em_branco": 2
}
```

Se não conseguir ler alguma resposta, marque como ilegível."""
    ),
    
    EtapaProcessamento.CORRIGIR: PromptTemplate(
        id="default_corrigir",
        nome="Correção - Padrão",
        etapa=EtapaProcessamento.CORRIGIR,
        descricao="Corrige as respostas comparando com o gabarito",
        is_padrao=True,
        variaveis=["questao", "resposta_esperada", "resposta_aluno", "criterios", "nota_maxima"],
        texto="""Você é um professor experiente corrigindo uma prova.

**Questão:**
{{questao}}

**Resposta Esperada:**
{{resposta_esperada}}

**Resposta do Aluno:**
{{resposta_aluno}}

**Critérios de Correção:**
{{criterios}}

**Nota Máxima:** {{nota_maxima}} pontos

Avalie a resposta e retorne um JSON:
```json
{
  "nota": 0.0,
  "nota_maxima": {{nota_maxima}},
  "percentual": 0,
  "status": "correta|parcial|incorreta|em_branco",
  "feedback": "Feedback detalhado e construtivo para o aluno",
  "pontos_positivos": ["O que o aluno acertou"],
  "pontos_melhorar": ["O que precisa melhorar"],
  "erros_conceituais": ["Erros de conceito identificados"],
  "habilidades_demonstradas": ["Habilidades que o aluno mostrou"],
  "habilidades_faltantes": ["Habilidades que precisam ser desenvolvidas"]
}
```

Seja justo, construtivo e educativo no feedback."""
    ),
    
    EtapaProcessamento.ANALISAR_HABILIDADES: PromptTemplate(
        id="default_analisar_habilidades",
        nome="Análise de Habilidades - Padrão",
        etapa=EtapaProcessamento.ANALISAR_HABILIDADES,
        descricao="Analisa habilidades demonstradas pelo aluno",
        is_padrao=True,
        variaveis=["correcoes", "nome_aluno", "materia"],
        texto="""Você é um especialista em avaliação educacional.

Analise o desempenho do aluno com base nas correções realizadas.

**Aluno:** {{nome_aluno}}
**Matéria:** {{materia}}

**Correções das questões:**
{{correcoes}}

Produza uma análise detalhada:
```json
{
  "aluno": "{{nome_aluno}}",
  "resumo_desempenho": "Resumo geral do desempenho",
  "nota_final": 0.0,
  "nota_maxima": 10.0,
  "percentual_acerto": 0,
  "habilidades": {
    "dominadas": [
      {"nome": "Habilidade X", "evidencia": "Acertou questões 1, 3, 5"}
    ],
    "em_desenvolvimento": [
      {"nome": "Habilidade Y", "evidencia": "Acertou parcialmente questão 2"}
    ],
    "nao_demonstradas": [
      {"nome": "Habilidade Z", "evidencia": "Errou questões 4, 6"}
    ]
  },
  "recomendacoes": [
    "Recomendação de estudo 1",
    "Recomendação de estudo 2"
  ],
  "pontos_fortes": ["Ponto forte 1"],
  "areas_atencao": ["Área que precisa de atenção"]
}
```"""
    ),
    
    EtapaProcessamento.GERAR_RELATORIO: PromptTemplate(
        id="default_gerar_relatorio",
        nome="Geração de Relatório - Padrão",
        etapa=EtapaProcessamento.GERAR_RELATORIO,
        descricao="Gera relatório final para o professor",
        is_padrao=True,
        variaveis=["nome_aluno", "materia", "atividade", "correcoes", "analise_habilidades", "nota_final"],
        texto="""Você é um assistente gerando um relatório de desempenho escolar.

**Aluno:** {{nome_aluno}}
**Matéria:** {{materia}}
**Atividade:** {{atividade}}
**Nota Final:** {{nota_final}}

**Correções detalhadas:**
{{correcoes}}

**Análise de habilidades:**
{{analise_habilidades}}

Gere um relatório completo em formato Markdown que inclua:

1. **Resumo Executivo** - Visão geral do desempenho
2. **Desempenho por Questão** - Tabela com nota de cada questão
3. **Análise de Habilidades** - O que domina e o que precisa melhorar
4. **Feedback Construtivo** - Mensagem motivadora para o aluno
5. **Recomendações** - Próximos passos de estudo

O relatório deve ser profissional mas acessível, adequado para ser compartilhado com o aluno e responsáveis."""
    ),
    
    EtapaProcessamento.CHAT_GERAL: PromptTemplate(
        id="default_chat",
        nome="Chat com Documentos - Padrão",
        etapa=EtapaProcessamento.CHAT_GERAL,
        descricao="Chat geral sobre os documentos",
        is_padrao=True,
        variaveis=["contexto_documentos", "pergunta"],
        texto="""Você é um assistente educacional com acesso aos seguintes documentos:

{{contexto_documentos}}

**Pergunta do usuário:**
{{pergunta}}

Responda de forma clara e útil, citando os documentos quando relevante."""
    )
}


class PromptManager:
    """Gerenciador de prompts com persistência em SQLite"""
    
    def __init__(self, db_path: str = "./data/database.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._setup_database()
        self._seed_prompts_padrao()
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _setup_database(self):
        conn = self._get_connection()
        c = conn.cursor()
        
        c.execute('''
            CREATE TABLE IF NOT EXISTS prompts (
                id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                etapa TEXT NOT NULL,
                texto TEXT NOT NULL,
                texto_sistema TEXT,
                descricao TEXT,
                is_padrao INTEGER DEFAULT 0,
                is_ativo INTEGER DEFAULT 1,
                materia_id TEXT,
                variaveis TEXT,
                versao INTEGER DEFAULT 1,
                criado_em TEXT,
                atualizado_em TEXT,
                criado_por TEXT
            )
        ''')
        
        # Histórico de versões
        c.execute('''
            CREATE TABLE IF NOT EXISTS prompts_historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prompt_id TEXT NOT NULL,
                versao INTEGER NOT NULL,
                texto TEXT NOT NULL,
                modificado_em TEXT,
                modificado_por TEXT,
                FOREIGN KEY (prompt_id) REFERENCES prompts(id)
            )
        ''')
        
        conn.commit()
        for column, col_type in [
            ("texto_sistema", "TEXT"),
            ("descricao", "TEXT"),
            ("is_padrao", "INTEGER DEFAULT 0"),
            ("is_ativo", "INTEGER DEFAULT 1"),
            ("materia_id", "TEXT"),
            ("variaveis", "TEXT"),
            ("versao", "INTEGER DEFAULT 1"),
            ("criado_em", "TEXT"),
            ("atualizado_em", "TEXT"),
            ("criado_por", "TEXT"),
        ]:
            self._ensure_column(conn, "prompts", column, col_type)
        conn.close()

    def _ensure_column(self, conn: sqlite3.Connection, table: str, column: str, col_type: str) -> None:
        c = conn.cursor()
        c.execute(f"PRAGMA table_info({table})")
        columns = {row[1] for row in c.fetchall()}
        if column not in columns:
            c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
            conn.commit()
    
    def _seed_prompts_padrao(self):
        """Insere prompts padrão se não existirem"""
        conn = self._get_connection()
        c = conn.cursor()
        
        for prompt in PROMPTS_PADRAO.values():
            c.execute('SELECT id FROM prompts WHERE id = ?', (prompt.id,))
            if not c.fetchone():
                c.execute('''
                    INSERT INTO prompts (id, nome, etapa, texto, texto_sistema, descricao, is_padrao, is_ativo, materia_id, variaveis, versao, criado_em, atualizado_em, criado_por)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    prompt.id, prompt.nome, prompt.etapa.value, prompt.texto, prompt.texto_sistema,
                    prompt.descricao, 1, 1, None, json.dumps(prompt.variaveis),
                    1, prompt.criado_em.isoformat(), prompt.atualizado_em.isoformat(), "sistema"
                ))
        
        conn.commit()
        conn.close()
    
    def criar_prompt(self, nome: str, etapa: EtapaProcessamento, texto: str,
                     texto_sistema: str = None,
                     descricao: str = None, materia_id: str = None,
                     variaveis: List[str] = None, criado_por: str = "usuario") -> PromptTemplate:
        """Cria um novo prompt"""
        import hashlib
        prompt_id = hashlib.sha256(f"{nome}_{etapa.value}_{datetime.now().timestamp()}".encode()).hexdigest()[:16]
        
        prompt = PromptTemplate(
            id=prompt_id,
            nome=nome,
            etapa=etapa,
            texto=texto,
            texto_sistema=texto_sistema,
            descricao=descricao,
            is_padrao=False,
            materia_id=materia_id,
            variaveis=variaveis or [],
            criado_por=criado_por
        )
        
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO prompts (id, nome, etapa, texto, texto_sistema, descricao, is_padrao, is_ativo, materia_id, variaveis, versao, criado_em, atualizado_em, criado_por)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            prompt.id, prompt.nome, prompt.etapa.value, prompt.texto, prompt.texto_sistema,
            prompt.descricao, 0, 1, prompt.materia_id, json.dumps(prompt.variaveis),
            1, prompt.criado_em.isoformat(), prompt.atualizado_em.isoformat(), prompt.criado_por
        ))
        conn.commit()
        conn.close()
        
        return prompt
    
    def get_prompt(self, prompt_id: str) -> Optional[PromptTemplate]:
        """Busca prompt por ID"""
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM prompts WHERE id = ?', (prompt_id,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            return None
        
        data = dict(row)
        data['variaveis'] = json.loads(data['variaveis']) if data['variaveis'] else []
        data['is_padrao'] = bool(data['is_padrao'])
        data['is_ativo'] = bool(data['is_ativo'])
        return PromptTemplate.from_dict(data)
    
    def get_prompt_padrao(self, etapa: EtapaProcessamento, materia_id: str = None) -> Optional[PromptTemplate]:
        """Busca o prompt padrão para uma etapa"""
        conn = self._get_connection()
        c = conn.cursor()
        
        # Primeiro tenta prompt específico da matéria
        if materia_id:
            c.execute('''
                SELECT * FROM prompts 
                WHERE etapa = ? AND materia_id = ? AND is_padrao = 1 AND is_ativo = 1
                ORDER BY versao DESC LIMIT 1
            ''', (etapa.value, materia_id))
            row = c.fetchone()
            if row:
                conn.close()
                data = dict(row)
                data['variaveis'] = json.loads(data['variaveis']) if data['variaveis'] else []
                return PromptTemplate.from_dict(data)
        
        # Senão, busca o global
        c.execute('''
            SELECT * FROM prompts 
            WHERE etapa = ? AND materia_id IS NULL AND is_padrao = 1 AND is_ativo = 1
            ORDER BY versao DESC LIMIT 1
        ''', (etapa.value,))
        row = c.fetchone()
        conn.close()
        
        if not row:
            return None
        
        data = dict(row)
        data['variaveis'] = json.loads(data['variaveis']) if data['variaveis'] else []
        return PromptTemplate.from_dict(data)
    
    def listar_prompts(self, etapa: EtapaProcessamento = None, materia_id: str = None,
                       apenas_ativos: bool = True) -> List[PromptTemplate]:
        """Lista prompts com filtros"""
        conn = self._get_connection()
        c = conn.cursor()
        
        query = 'SELECT * FROM prompts WHERE 1=1'
        params = []
        
        if etapa:
            query += ' AND etapa = ?'
            params.append(etapa.value)
        
        if materia_id:
            query += ' AND (materia_id = ? OR materia_id IS NULL)'
            params.append(materia_id)
        
        if apenas_ativos:
            query += ' AND is_ativo = 1'
        
        query += ' ORDER BY is_padrao DESC, nome'
        
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        
        prompts = []
        for row in rows:
            data = dict(row)
            data['variaveis'] = json.loads(data['variaveis']) if data['variaveis'] else []
            data['is_padrao'] = bool(data['is_padrao'])
            data['is_ativo'] = bool(data['is_ativo'])
            prompts.append(PromptTemplate.from_dict(data))
        
        return prompts
    
    def atualizar_prompt(self, prompt_id: str, texto: str = None, nome: str = None,
                         texto_sistema: str = None,
                         descricao: str = None, modificado_por: str = "usuario") -> Optional[PromptTemplate]:
        """Atualiza um prompt, salvando versão anterior no histórico"""
        prompt_atual = self.get_prompt(prompt_id)
        if not prompt_atual:
            return None
        
        conn = self._get_connection()
        c = conn.cursor()
        
        # Salvar no histórico
        c.execute('''
            INSERT INTO prompts_historico (prompt_id, versao, texto, modificado_em, modificado_por)
            VALUES (?, ?, ?, ?, ?)
        ''', (prompt_id, prompt_atual.versao, prompt_atual.texto, datetime.now().isoformat(), modificado_por))
        
        # Atualizar prompt
        nova_versao = prompt_atual.versao + 1
        updates = ['versao = ?', 'atualizado_em = ?']
        params = [nova_versao, datetime.now().isoformat()]
        
        if texto:
            updates.append('texto = ?')
            params.append(texto)
        if texto_sistema is not None:
            updates.append('texto_sistema = ?')
            params.append(texto_sistema)
        if nome:
            updates.append('nome = ?')
            params.append(nome)
        if descricao is not None:
            updates.append('descricao = ?')
            params.append(descricao)
        
        params.append(prompt_id)
        
        c.execute(f"UPDATE prompts SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        conn.close()
        
        return self.get_prompt(prompt_id)
    
    def get_historico(self, prompt_id: str) -> List[Dict[str, Any]]:
        """Retorna histórico de versões de um prompt"""
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('''
            SELECT * FROM prompts_historico 
            WHERE prompt_id = ? 
            ORDER BY versao DESC
        ''', (prompt_id,))
        rows = c.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def definir_padrao(self, prompt_id: str, etapa: EtapaProcessamento, materia_id: str = None) -> bool:
        """Define um prompt como padrão para uma etapa"""
        conn = self._get_connection()
        c = conn.cursor()
        
        # Remove padrão anterior
        if materia_id:
            c.execute('UPDATE prompts SET is_padrao = 0 WHERE etapa = ? AND materia_id = ?', (etapa.value, materia_id))
        else:
            c.execute('UPDATE prompts SET is_padrao = 0 WHERE etapa = ? AND materia_id IS NULL', (etapa.value,))
        
        # Define novo padrão
        c.execute('UPDATE prompts SET is_padrao = 1 WHERE id = ?', (prompt_id,))
        
        conn.commit()
        conn.close()
        return True
    
    def deletar_prompt(self, prompt_id: str) -> bool:
        """Deleta um prompt (soft delete - marca como inativo)"""
        conn = self._get_connection()
        c = conn.cursor()
        c.execute('UPDATE prompts SET is_ativo = 0 WHERE id = ? AND is_padrao = 0', (prompt_id,))
        affected = c.rowcount
        conn.commit()
        conn.close()
        return affected > 0
    
    def duplicar_prompt(self, prompt_id: str, novo_nome: str, materia_id: str = None) -> Optional[PromptTemplate]:
        """Duplica um prompt existente"""
        original = self.get_prompt(prompt_id)
        if not original:
            return None
        
        return self.criar_prompt(
            nome=novo_nome,
            etapa=original.etapa,
            texto=original.texto,
            texto_sistema=original.texto_sistema,
            descricao=f"Cópia de: {original.nome}",
            materia_id=materia_id,
            variaveis=original.variaveis
        )


# Instância global
prompt_manager = PromptManager()
