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
        texto = self._render_texto(self.texto, **kwargs)
        self._verificar_variaveis_nao_substituidas(texto, "prompt_usuario")
        return texto

    def render_sistema(self, **kwargs) -> str:
        """Renderiza o prompt de sistema substituindo variáveis"""
        if not self.texto_sistema:
            return ""
        texto = self._render_texto(self.texto_sistema, **kwargs)
        self._verificar_variaveis_nao_substituidas(texto, "prompt_sistema")
        return texto

    @staticmethod
    def _render_texto(texto: str, **kwargs) -> str:
        """Renderiza um texto substituindo variáveis"""
        for var, valor in kwargs.items():
            texto = texto.replace(f"{{{{{var}}}}}", str(valor))
        return texto

    def _verificar_variaveis_nao_substituidas(self, texto: str, tipo: str) -> None:
        """Verifica e loga variáveis que não foram substituídas"""
        import re
        import logging
        nao_substituidas = re.findall(r'\{\{(\w+)\}\}', texto)
        if nao_substituidas:
            logging.warning(
                f"[{self.etapa.value}] Variáveis não substituídas em {tipo}: {nao_substituidas}"
            )


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

INSTRUÇÃO CRÍTICA: Retorne APENAS o JSON válido, sem texto adicional, explicações ou formatação Markdown. O resultado deve ser um JSON parseável que começa com { e termina com }.

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
      "habilidades": ["habilidade1", "habilidade2"],
      "tipo_raciocinio": "memoria|aplicacao|analise|sintese|avaliacao"
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
      "conceito_central": "Conceito pedagógico principal testado por esta questão (ex: 'conservação de energia', 'interpretação de gráficos')",
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

Analise o documento anexado (PDF) da prova respondida pelo aluno e extraia suas respostas.

**Aluno:** {{nome_aluno}}

**Questões da prova:**
{{questoes_extraidas}}

INSTRUÇÃO CRÍTICA: Retorne APENAS o JSON válido, sem texto adicional, explicações ou formatação Markdown. O resultado deve ser um JSON parseável que começa com { e termina com }.

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
      "observacoes": "Qualquer observação relevante",
      "raciocinio_parcial": "Descreva sinais de raciocínio do aluno identificados na resposta, mesmo que errada (ex: 'aplicou F=ma corretamente mas inverteu sinal', 'começou a resolução mas não concluiu'). null se não identificado."
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
        descricao="Corrige as respostas comparando com o gabarito com análise narrativa pedagógica",
        is_padrao=True,
        variaveis=["questao", "resposta_esperada", "resposta_aluno", "criterios", "nota_maxima"],
        texto_sistema="""Você é um professor experiente com profundo entendimento pedagógico, especializado em identificar o raciocínio por trás das respostas dos alunos — não apenas se estão certas ou erradas.

Sua função vai além da nota: você identifica o que o aluno estava pensando, classifica o tipo de erro com precisão pedagógica, e avalia o potencial demonstrado. Sua análise serve tanto ao professor (diagnóstico preciso) quanto ao aluno (compreensão do próprio processo de aprendizado).

Princípios que guiam seu trabalho:
- Um erro de cálculo NÃO é um erro conceitual — esta distinção importa para o próximo passo do aluno
- Um aluno que deixa em branco pode não ter conteúdo, ou pode ter bloqueado — contexto importa
- O raciocínio parcialmente correto revela mais do que a resposta final errada
- Linguagem construtiva: critique o erro específico, nunca o aluno como pessoa
- A narrativa não é um resumo do erro — é uma interpretação pedagógica do que aconteceu""",
        texto="""Corrija a resposta do aluno com rigor e sensibilidade pedagógica.

**Questão:**
{{questao}}

**Resposta Esperada (gabarito):**
{{resposta_esperada}}

**Resposta do Aluno:**
{{resposta_aluno}}

**Critérios de Correção:**
{{criterios}}

**Nota Máxima:** {{nota_maxima}} pontos

---

**INSTRUÇÃO CRÍTICA:** Retorne APENAS JSON válido, sem texto adicional antes ou depois.

```json
{
  "nota": 0.0,
  "nota_maxima": {{nota_maxima}},
  "percentual": 0,
  "status": "correta|parcial|incorreta|em_branco",
  "feedback": "Feedback direto e construtivo — o que o aluno fez de certo, o que errou e como melhorar",
  "pontos_positivos": ["O que o aluno demonstrou corretamente"],
  "pontos_melhorar": ["O que precisa melhorar, de forma específica e acionável"],
  "erros_conceituais": ["Erros de conceito identificados, se houver"],
  "habilidades_demonstradas": ["Habilidades que o aluno evidenciou nesta resposta"],
  "habilidades_faltantes": ["Habilidades ausentes que explicariam a resposta correta"],
  "narrativa_correcao": "## Questão — Análise Pedagógica\n\n**O que o aluno tentou fazer:** [Descreva o raciocínio com precisão — o que o aluno estava pensando, qual estratégia tentou, onde o processo estava certo antes de desviar. Seja específico: não 'o aluno errou o cálculo' mas 'o aluno aplicou corretamente a fórmula PV=nRT mas confundiu a unidade de pressão, usando atm em vez de Pa']\n\n**Tipo de erro:** [Classifique em UMA categoria e explique: CONCEITUAL (entende errado o princípio) / CÁLCULO (processo certo, operação errada) / INTERPRETAÇÃO (não leu o que a questão pedia) / OMISSÃO (deixou em branco ou incompleto) / UNIDADE (conversão ou grandeza errada) / APLICAÇÃO (sabe o conceito mas aplica no contexto errado)]\n\n**Potencial:** [Alto/Médio/Baixo — avalie com base no raciocínio demonstrado, não apenas na nota. Um aluno que errou só a unidade pode ter potencial Alto. Linguagem direta e construtiva, adequada para o aluno ler e se motivar]"
}
```"""
    ),
    
    EtapaProcessamento.ANALISAR_HABILIDADES: PromptTemplate(
        id="default_analisar_habilidades",
        nome="Análise de Habilidades - Padrão",
        etapa=EtapaProcessamento.ANALISAR_HABILIDADES,
        descricao="Analisa padrões de aprendizado do aluno com síntese narrativa pedagógica",
        is_padrao=True,
        variaveis=["correcoes", "nome_aluno", "materia"],
        texto_sistema="""Você é um especialista em avaliação educacional com olhar apurado para padrões de aprendizado — não apenas para desempenho pontual. Você analisa o conjunto da obra: o que o aluno revelou sobre si mesmo ao longo de toda a prova.

Sua missão é identificar padrões, não inventariar erros. A diferença entre uma análise pedagógica real e um checklist de habilidades é que a análise pedagógica conta uma história coerente sobre quem é este aluno como aprendiz.

Princípios fundamentais:
- Consistência de erros é informação valiosa — erros aleatórios e erros sistemáticos têm causas e tratamentos diferentes
- Distinguir "não sabe o conteúdo" (deixou em branco) de "sabe mas erra na execução" (respondeu errado)
- Tentativas de transferência de conceitos entre domínios revelam nível de compreensão profunda
- O que o aluno tentou fazer é tão importante quanto o resultado final
- Esforço sem conteúdo e conteúdo sem organização são problemas diferentes que exigem intervenções diferentes
- Seu texto deve poder ser lido pelo professor como diagnóstico e pelo aluno como espelho""",
        texto="""Analise o desempenho de {{nome_aluno}} em {{materia}} e produza uma síntese de padrões de aprendizado.

**Aluno:** {{nome_aluno}}
**Matéria:** {{materia}}

**Correções das questões:**
{{correcoes}}

---

Sua análise tem duas partes: (1) dados tabulares de habilidades para o professor, e (2) narrativa de padrões para diagnóstico pedagógico.

**INSTRUÇÃO CRÍTICA:** Retorne APENAS JSON válido, sem texto adicional antes ou depois.

```json
{
  "aluno": "{{nome_aluno}}",
  "resumo_desempenho": "Uma frase que capture o perfil central deste aluno — não apenas a nota",
  "nota_final": 0.0,
  "nota_maxima": 10.0,
  "percentual_acerto": 0,
  "habilidades": {
    "dominadas": [
      {"nome": "Nome da habilidade", "evidencia": "Questões específicas que demonstram domínio"}
    ],
    "em_desenvolvimento": [
      {"nome": "Nome da habilidade", "evidencia": "Questões com acerto parcial — o que foi e o que não foi"}
    ],
    "nao_demonstradas": [
      {"nome": "Nome da habilidade", "evidencia": "Questões em branco ou com erro total — e a distinção: ausência de conteúdo ou erro conceitual"}
    ]
  },
  "recomendacoes": [
    "Recomendação específica e acionável — não genérica",
    "Segunda recomendação baseada em padrão identificado"
  ],
  "pontos_fortes": ["Competência real demonstrada, com evidência"],
  "areas_atencao": ["Área específica, com tipo de intervenção sugerida"],
  "narrativa_habilidades": "## Perfil de Aprendizado — {{nome_aluno}}\n\n**Consistência:** [Descreva se os erros são aleatórios ou sistemáticos. Erros sistemáticos = lacuna específica. Erros aleatórios = instabilidade de execução. Cite questões concretas como evidência. Seja específico: não 'errou em matemática' mas 'em 3 das 4 questões de cálculo, o raciocínio estava correto até o passo de conversão de unidades']\n\n**O que {{nome_aluno}} tentou fazer:** [Descreva as estratégias usadas ao longo da prova — o que o aluno tentou, não só o que errou. Se tentou aplicar conceito de um domínio em outro, destaque isso. Se desenvolveu estratégia própria que quase funcionou, reconheça. Esta seção deve revelar o aprendiz por trás das respostas]\n\n**Esforço vs. Conhecimento:** [Questões em branco = provável ausência de conteúdo, não de esforço. Questões respondidas errado = conceito presente mas incorreto, ou execução falhou. Questões parciais = conceito presente com lacuna específica. Diferencie cada caso nas evidências desta prova]\n\n**Recomendação Principal:** [Uma recomendação específica, prática e priorizada para este aluno neste momento — baseada nos padrões acima. Uma recomendação bem calibrada vale mais que dez genéricas]"
}
```"""
    ),
    
    EtapaProcessamento.GERAR_RELATORIO: PromptTemplate(
        id="default_gerar_relatorio",
        nome="Geração de Relatório - Padrão",
        etapa=EtapaProcessamento.GERAR_RELATORIO,
        descricao="Gera relatório narrativo holístico que começa pelo quadro geral do aluno",
        is_padrao=True,
        variaveis=["nome_aluno", "materia", "atividade", "correcoes", "analise_habilidades", "nota_final"],
        texto_sistema="""Você é um autor de relatórios pedagógicos com habilidade para transformar dados de desempenho em narrativas coerentes e construtivas — relatórios que professores mostram aos alunos e pais com confiança.

Seu relatório deve ler como uma carta de avaliação cuidadosa, não como uma planilha preenchida. A nota é um dado — o relatório é uma interpretação. Sua função é dar sentido aos dados técnicos das correções e da análise de habilidades, tecendo-os numa narrativa unificada sobre quem é este aluno como aprendiz.

Princípios inegociáveis:
- Comece sempre pelo quadro geral (visão do todo), nunca pelos detalhes
- A visão geral responde: quem é este aluno? o que esta prova revelou sobre ele?
- Afunile progressivamente: quadro geral → padrões → questões específicas → recomendações
- Linguagem que o aluno de ensino médio possa ler e entender — sem jargão técnico excessivo
- Construtivo: toda crítica vem acompanhada de um caminho para melhorar
- O relatório deve fazer o aluno querer continuar, não desistir""",
        texto="""Gere o relatório de desempenho de {{nome_aluno}} em {{atividade}} de {{materia}}.

**Aluno:** {{nome_aluno}}
**Matéria:** {{materia}}
**Atividade:** {{atividade}}
**Nota Final:** {{nota_final}}

**Correções detalhadas por questão:**
{{correcoes}}

**Análise de habilidades e padrões:**
{{analise_habilidades}}

---

Produza um JSON com dois produtos: (1) conteudo em Markdown para armazenamento, e (2) relatorio_narrativo como narrativa holística.

**INSTRUÇÃO CRÍTICA:** Retorne APENAS JSON válido, sem texto adicional antes ou depois.

{
  "conteudo": "# Relatório de Desempenho — {{nome_aluno}}\\n\\n**{{materia}} — {{atividade}}**\\n**Nota: {{nota_final}}**\\n\\n## Resumo\\n[Síntese do desempenho]\\n\\n## Desempenho por Questão\\n[Tabela ou lista estruturada]\\n\\n## Análise de Habilidades\\n[Habilidades dominadas, em desenvolvimento, ausentes]\\n\\n## Recomendações\\n[Lista de próximos passos]",
  "resumo_executivo": "Uma frase que captura quem é este aluno nesta prova — não apenas a nota",
  "nota_final": "{{nota_final}}",
  "aluno": "{{nome_aluno}}",
  "materia": "{{materia}}",
  "atividade": "{{atividade}}",
  "relatorio_narrativo": "## Visão Geral\\n\\n[OBRIGATÓRIO: comece aqui. Quem é {{nome_aluno}} como estudante nesta prova? O que a nota {{nota_final}} revela — e o que ela esconde? Esta seção deve ler como o parágrafo de abertura de uma carta do professor para os pais. Não mencione questões específicas aqui — fale sobre o aluno]\\n\\n## O que a Prova Revelou\\n\\n[Afunile para os padrões: combine a análise de habilidades com as correções para construir um retrato coerente. Quais questões revelaram pontos fortes? Onde o aluno travou? Se houver padrão de erro (ex: sempre acerta o raciocínio mas erra a unidade), destaque-o aqui como insight — não como crítica]\\n\\n## Para {{nome_aluno}}\\n\\n[Seção em linguagem direta ao aluno, na segunda pessoa. Construtiva, específica, sem jargão. O que você quer que {{nome_aluno}} leve desta prova? Uma ou duas recomendações práticas que ele pode aplicar já no próximo estudo. Termine com algo que motive a continuar]"
}"""
    ),
    
    EtapaProcessamento.CHAT_GERAL: PromptTemplate(
        id="default_chat",
        nome="Chat com Documentos - Padrão",
        etapa=EtapaProcessamento.CHAT_GERAL,
        descricao="Chat geral sobre os documentos",
        is_padrao=True,
        variaveis=["contexto_documentos", "pergunta"],
        texto="""Você é um assistente educacional com acesso aos seguintes documentos sobre o desempenho do aluno:

{{contexto_documentos}}

**Sobre os documentos disponíveis:**
Os documentos podem incluir análises pedagógicas narrativas em Markdown, geradas automaticamente pelos stages analíticos do pipeline:
- **Correção narrativa** (correcao_narrativa): análise pedagógica por questão — raciocínio do aluno, tipo de erro, potencial
- **Análise de habilidades narrativa** (analise_habilidades_narrativa): síntese de padrões de aprendizado — consistência, esforço vs. conhecimento
- **Relatório narrativo** (relatorio_narrativo): relatório holístico que começa pelo quadro geral do aluno

Quando disponíveis, esses documentos narrativos contêm análise pedagógica profunda e devem ser priorizados para responder perguntas sobre o raciocínio do aluno, padrões de erro e recomendações pedagógicas.

**Pergunta do professor:**
{{pergunta}}

Responda de forma clara, pedagógica e construtiva, citando os documentos quando relevante. Priorize as análises narrativas quando a pergunta envolver diagnóstico pedagógico."""
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
        """Insere prompts padrão se não existirem; atualiza texto e texto_sistema se já existirem."""
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
            else:
                # Sincroniza texto e texto_sistema do PROMPTS_PADRAO — garante que restarts
                # após atualizações de código propaguem novos prompts para o banco existente.
                c.execute(
                    'UPDATE prompts SET texto = ?, texto_sistema = ?, atualizado_em = ? WHERE id = ?',
                    (prompt.texto, prompt.texto_sistema, datetime.now().isoformat(), prompt.id)
                )

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
