"""
=================================================================
MÓDULO DE TESTES - Gerador de Dados Fictícios
=================================================================

Este módulo cria dados de teste para o sistema Prova AI, incluindo:
- Matérias variadas
- Turmas com diferentes configurações
- Alunos com nomes brasileiros realistas
- Atividades (provas, trabalhos, exercícios)
- Documentos de todos os tipos
- Casos especiais para testar avisos e erros

Execute com: python test_data_generator.py

Opções:
  --limpar    Remove todos os dados de teste antes de criar novos
  --mini      Cria apenas dados mínimos (1 matéria, 1 turma, 3 alunos)
  --completo  Cria dataset completo para testes extensivos
"""

import sys
import os
import io
import json
import random
import shutil
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import argparse

# Corrigir encoding do console Windows para suportar UTF-8
# Only when running as script (not when imported by pytest)
if sys.platform == 'win32' and __name__ == '__main__':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Adicionar o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from storage import StorageManager, storage
    from models import TipoDocumento, NivelEnsino

except ImportError as e:
    print(f"ERRO ao importar: {e}")
    sys.exit(1)


# =================================================================
# DADOS FICTÍCIOS
# =================================================================

NOMES_PROPRIOS = [
    "Ana", "Beatriz", "Carlos", "Daniel", "Eduardo", "Fernanda", "Gabriel",
    "Helena", "Igor", "Julia", "Kevin", "Larissa", "Marcos", "Natália",
    "Otávio", "Paula", "Rafael", "Sofia", "Thiago", "Valentina", "William",
    "Yasmin", "Arthur", "Bianca", "Caio", "Diana", "Enzo", "Flávia",
    "Gustavo", "Isabela", "João", "Kamila", "Leonardo", "Mariana", "Nicolas",
    "Olivia", "Pedro", "Rebeca", "Samuel", "Tatiana", "Vinícius", "Zoe"
]

SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves",
    "Pereira", "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho",
    "Almeida", "Lopes", "Soares", "Fernandes", "Vieira", "Barbosa", "Rocha",
    "Dias", "Nascimento", "Andrade", "Moreira", "Nunes", "Marques", "Machado",
    "Mendes", "Freitas", "Cardoso", "Ramos", "Gonçalves", "Santana", "Teixeira"
]

MATERIAS_CONFIG = [
    {
        "nome": "Matemática",
        "descricao": "Álgebra, geometria, aritmética e estatística",
        "nivel": NivelEnsino.FUNDAMENTAL_2,
        "turmas": ["9º Ano A", "9º Ano B", "8º Ano A"],
        "atividades": [
            {"nome": "Prova 1 - Equações do 1º Grau", "tipo": "prova", "nota_maxima": 10},
            {"nome": "Prova 2 - Geometria Plana", "tipo": "prova", "nota_maxima": 10},
            {"nome": "Trabalho - Estatística", "tipo": "trabalho", "nota_maxima": 5},
            {"nome": "Lista de Exercícios - Frações", "tipo": "exercicio", "nota_maxima": 2}
        ]
    },
    {
        "nome": "Português",
        "descricao": "Gramática, interpretação de texto e redação",
        "nivel": NivelEnsino.FUNDAMENTAL_2,
        "turmas": ["9º Ano A", "9º Ano B"],
        "atividades": [
            {"nome": "Prova 1 - Interpretação de Texto", "tipo": "prova", "nota_maxima": 10},
            {"nome": "Redação - Dissertação Argumentativa", "tipo": "trabalho", "nota_maxima": 10},
            {"nome": "Prova 2 - Gramática", "tipo": "prova", "nota_maxima": 10}
        ]
    },
    {
        "nome": "Ciências",
        "descricao": "Física, química e biologia básicas",
        "nivel": NivelEnsino.FUNDAMENTAL_2,
        "turmas": ["9º Ano A", "8º Ano A"],
        "atividades": [
            {"nome": "Prova 1 - Sistema Solar", "tipo": "prova", "nota_maxima": 10},
            {"nome": "Relatório - Experimento Densidade", "tipo": "trabalho", "nota_maxima": 8}
        ]
    },
    {
        "nome": "História",
        "descricao": "História do Brasil e mundial",
        "nivel": NivelEnsino.FUNDAMENTAL_2,
        "turmas": ["9º Ano A"],
        "atividades": [
            {"nome": "Prova 1 - Era Vargas", "tipo": "prova", "nota_maxima": 10},
            {"nome": "Seminário - Revolução Industrial", "tipo": "trabalho", "nota_maxima": 10}
        ]
    },
    {
        "nome": "Inglês",
        "descricao": "Língua inglesa - gramática e conversação",
        "nivel": NivelEnsino.FUNDAMENTAL_2,
        "turmas": ["9º Ano A", "9º Ano B"],
        "atividades": [
            {"nome": "Test 1 - Verb Tenses", "tipo": "prova", "nota_maxima": 10},
            {"nome": "Reading Comprehension", "tipo": "exercicio", "nota_maxima": 5}
        ]
    }
]

# Configuração menor para deploy rápido (Render startup / demonstração)
MATERIAS_CONFIG_MINI = [
    {
        "nome": "Matemática",
        "descricao": "Álgebra, geometria, aritmética e estatística",
        "nivel": NivelEnsino.FUNDAMENTAL_2,
        "turmas": ["9º Ano A"],
        "atividades": [
            {"nome": "Prova 1 - Equações do 1º Grau", "tipo": "prova", "nota_maxima": 10},
            {"nome": "Trabalho - Estatística", "tipo": "trabalho", "nota_maxima": 5}
        ]
    },
    {
        "nome": "Português",
        "descricao": "Gramática, interpretação de texto e redação",
        "nivel": NivelEnsino.FUNDAMENTAL_2,
        "turmas": ["9º Ano A"],
        "atividades": [
            {"nome": "Prova 1 - Interpretação de Texto", "tipo": "prova", "nota_maxima": 10},
            {"nome": "Redação - Dissertação Argumentativa", "tipo": "trabalho", "nota_maxima": 10}
        ]
    },
    {
        "nome": "Ciências",
        "descricao": "Física, química e biologia básicas",
        "nivel": NivelEnsino.FUNDAMENTAL_2,
        "turmas": ["9º Ano A"],
        "atividades": [
            {"nome": "Prova 1 - Sistema Solar", "tipo": "prova", "nota_maxima": 10}
        ]
    }
]

# Conteúdos de exemplo para documentos
ENUNCIADO_EXEMPLO = """
ESCOLA MODELO - AVALIAÇÃO DE {materia}
{turma} - {data}

Nome: _________________________________ Nº: _____

INSTRUÇÕES:
- Leia atentamente cada questão antes de responder
- Use caneta azul ou preta
- Não é permitido o uso de calculadora (exceto se indicado)
- Boa prova!

═══════════════════════════════════════════════════════════════

QUESTÃO 1 (2,0 pontos)
{questao_1}

QUESTÃO 2 (2,0 pontos)
{questao_2}

QUESTÃO 3 (3,0 pontos)
{questao_3}

QUESTÃO 4 (3,0 pontos)
{questao_4}

═══════════════════════════════════════════════════════════════
"""

QUESTOES_POR_MATERIA = {
    "Matemática": [
        "Resolva a equação: 3x + 7 = 22",
        "Calcule a área de um triângulo com base 8cm e altura 5cm.",
        "Um produto custa R$ 150,00 e está com 20% de desconto. Qual o valor final?",
        "Simplifique a fração 48/64 até sua forma irredutível."
    ],
    "Português": [
        "Identifique o sujeito e o predicado na frase: 'Os alunos estudaram muito para a prova.'",
        "Reescreva a frase no plural: 'O cidadão brasileiro é resiliente.'",
        "Classifique as orações do período: 'Quando chegou, todos aplaudiram.'",
        "Analise sintaticamente: 'Maria deu um presente ao amigo.'"
    ],
    "Ciências": [
        "Explique a diferença entre célula animal e vegetal.",
        "Descreva o processo de fotossíntese.",
        "O que é densidade? Dê um exemplo prático.",
        "Liste os planetas do Sistema Solar em ordem de distância do Sol."
    ],
    "História": [
        "Quais foram as principais causas da Revolução Francesa?",
        "Descreva o período do Estado Novo no Brasil.",
        "Compare o feudalismo com o capitalismo.",
        "Explique a importância da Revolução Industrial."
    ],
    "Inglês": [
        "Complete with the correct verb tense: She ___ (study) English since 2020.",
        "Translate to English: 'Eu gostaria de viajar para Londres.'",
        "Write a sentence using the Present Perfect.",
        "What is the difference between 'make' and 'do'? Give examples."
    ]
}

GABARITO_EXEMPLO = """
GABARITO - {atividade}
{materia} - {turma}

QUESTÃO 1 (2,0 pontos)
Resposta esperada: {resp_1}
Critérios: Demonstrar o passo a passo. Resposta correta sem desenvolvimento: 1,0 ponto.

QUESTÃO 2 (2,0 pontos)
Resposta esperada: {resp_2}
Critérios: Uso correto da fórmula. Unidades corretas.

QUESTÃO 3 (3,0 pontos)
Resposta esperada: {resp_3}
Critérios: Raciocínio lógico (1,5), cálculo correto (1,5).

QUESTÃO 4 (3,0 pontos)
Resposta esperada: {resp_4}
Critérios: Explicação clara e completa.
"""

RESPOSTAS_POR_MATERIA = {
    "Matemática": ["x = 5", "Área = 20 cm²", "R$ 120,00", "3/4"],
    "Português": [
        "Sujeito: Os alunos; Predicado: estudaram muito para a prova",
        "Os cidadãos brasileiros são resilientes",
        "Oração subordinada adverbial temporal + oração principal",
        "Maria (sujeito) deu (VTDI) um presente (OD) ao amigo (OI)"
    ],
    "Ciências": [
        "Célula vegetal tem parede celular e cloroplastos; animal não",
        "6CO2 + 6H2O + luz -> C6H12O6 + 6O2",
        "Densidade = massa/volume. Ex: gelo flutua na água",
        "Mercúrio, Vênus, Terra, Marte, Júpiter, Saturno, Urano, Netuno"
    ],
    "História": [
        "Crise econômica, desigualdade social, ideias iluministas",
        "Período ditatorial de Getúlio Vargas (1937-1945)",
        "Feudalismo: terra; Capitalismo: capital e lucro",
        "Mecanização da produção, urbanização, mudanças sociais"
    ],
    "Inglês": [
        "has been studying",
        "I would like to travel to London",
        "I have lived here for 10 years",
        "Make: criar algo; Do: realizar ação. Make a cake, Do homework"
    ]
}

# Tipos de problemas para testar avisos
PROBLEMAS_DOCUMENTO = {
    "em_branco": {
        "descricao": "Documento completamente em branco",
        "conteudo": "",
        "metadata": {"aviso": "documento_vazio"}
    },
    "ilegivel": {
        "descricao": "Documento com texto ilegível/corrompido",
        "conteudo": "░░░▒▒▒▓▓▓███ ??? @@@ ### ░░░",
        "metadata": {"aviso": "texto_ilegivel", "confianca_ocr": 0.15}
    },
    "incompleto": {
        "descricao": "Documento com questões faltando",
        "conteudo": "Questão 1: Resposta aqui\n\n[PÁGINA 2 NÃO ENCONTRADA]\n\nQuestão 4: Outra resposta",
        "metadata": {"aviso": "questoes_faltando", "questoes_encontradas": [1, 4], "questoes_esperadas": [1, 2, 3, 4]}
    },
    "baixa_qualidade": {
        "descricao": "Documento com qualidade de imagem muito baixa",
        "conteudo": "qu3st40 1: r3sp0st4 4qu1\nqu3st40 2: n40 c0ns1g0 l3r",
        "metadata": {"aviso": "baixa_qualidade", "confianca_ocr": 0.45}
    },
    "formato_errado": {
        "descricao": "Documento em formato inesperado",
        "conteudo": "<html><body>Isso não é uma prova</body></html>",
        "metadata": {"aviso": "formato_inesperado", "formato_detectado": "html"}
    },
    "sem_identificacao": {
        "descricao": "Prova do aluno sem nome/identificação",
        "conteudo": "Questão 1: 42\nQuestão 2: A alternativa correta é B\nQuestão 3: Não sei",
        "metadata": {"aviso": "sem_identificacao_aluno"}
    }
}


# =================================================================
# CLASSE GERADORA
# =================================================================

class TestDataGenerator:
    """Gerador de dados de teste para o sistema Prova AI"""
    
    def __init__(self, storage: StorageManager, verbose: bool = True):
        self.storage = storage
        self.verbose = verbose
        
        # Cache dos IDs criados
        self.materias_criadas: Dict[str, Any] = {}
        self.turmas_criadas: Dict[str, Any] = {}
        self.alunos_criados: List[Any] = []
        self.atividades_criadas: Dict[str, Any] = {}
        self.documentos_criados: List[Dict] = []
        
        # Estatísticas
        self.stats = {
            "materias": 0,
            "turmas": 0,
            "alunos": 0,
            "vinculos": 0,
            "atividades": 0,
            "documentos": 0,
            "documentos_problematicos": 0
        }
    
    def log(self, msg: str, indent: int = 0):
        """Log com indentação"""
        if self.verbose:
            print("  " * indent + msg)
    
    def gerar_nome_completo(self) -> str:
        """Gera um nome brasileiro realista"""
        nome = random.choice(NOMES_PROPRIOS)
        sobrenome1 = random.choice(SOBRENOMES)
        sobrenome2 = random.choice(SOBRENOMES)
        
        # 50% chance de ter dois sobrenomes
        if random.random() > 0.5:
            return f"{nome} {sobrenome1} {sobrenome2}"
        return f"{nome} {sobrenome1}"
    
    def gerar_email(self, nome: str) -> str:
        """Gera email baseado no nome"""
        nome_limpo = nome.lower().split()[0]
        dominio = random.choice(["gmail.com", "hotmail.com", "outlook.com", "yahoo.com"])
        numero = random.randint(1, 999)
        return f"{nome_limpo}{numero}@{dominio}"
    
    def gerar_matricula(self, ano: int = 2024) -> str:
        """Gera número de matrícula"""
        return f"{ano}{random.randint(1000, 9999)}"
    
    # -----------------------------------------------------------------
    # CRIAÇÃO DE ENTIDADES
    # -----------------------------------------------------------------
    
    def criar_materias(self, configs: List[Dict] = None):
        """Cria matérias com suas turmas e atividades"""
        configs = configs or MATERIAS_CONFIG_MINI
        
        self.log("[+] Criando matérias...")
        
        for config in configs:
            # Criar matéria
            materia = self.storage.criar_materia(
                nome=config["nome"],
                descricao=config.get("descricao"),
                nivel=config.get("nivel", NivelEnsino.FUNDAMENTAL_2)
            )
            # Tag as fantasy data
            self.storage.atualizar_materia(materia.id, metadata={"criado_por": "test_generator"})
            self.materias_criadas[config["nome"]] = materia
            self.stats["materias"] += 1
            self.log(f"[v] {materia.nome}", indent=1)
            
            # Criar turmas
            for turma_nome in config.get("turmas", []):
                turma = self.storage.criar_turma(
                    materia_id=materia.id,
                    nome=turma_nome,
                    ano_letivo=2024,
                    periodo=random.choice(["Manhã", "Tarde"])
                )
                key = f"{config['nome']}_{turma_nome}"
                self.turmas_criadas[key] = turma
                self.stats["turmas"] += 1
                self.log(f"  -> Turma: {turma_nome}", indent=1)
                
                # Criar atividades
                for ativ_config in config.get("atividades", []):
                    data_aplicacao = datetime.now() - timedelta(days=random.randint(1, 60))
                    atividade = self.storage.criar_atividade(
                        turma_id=turma.id,
                        nome=ativ_config["nome"],
                        tipo=ativ_config.get("tipo", "prova"),
                        data_aplicacao=data_aplicacao,
                        nota_maxima=ativ_config.get("nota_maxima", 10.0)
                    )
                    ativ_key = f"{key}_{ativ_config['nome']}"
                    self.atividades_criadas[ativ_key] = {
                        "atividade": atividade,
                        "materia": config["nome"],
                        "turma": turma_nome
                    }
                    self.stats["atividades"] += 1
    
    def criar_alunos(self, quantidade: int = 20):
        """Cria alunos"""
        self.log(f"[U] Criando {quantidade} alunos...")
        
        for i in range(quantidade):
            nome = self.gerar_nome_completo()
            email = self.gerar_email(nome)
            matricula = self.gerar_matricula()
            
            aluno = self.storage.criar_aluno(
                nome=nome,
                email=email,
                matricula=matricula
            )
            # Tag as fantasy data
            self.storage.atualizar_aluno(aluno.id, metadata={"criado_por": "test_generator"})
            self.alunos_criados.append(aluno)
            self.stats["alunos"] += 1
        
        self.log(f"[v] {quantidade} alunos criados", indent=1)
    
    def vincular_alunos_turmas(self, alunos_por_turma: int = 10):
        """Vincula alunos às turmas de forma realista"""
        self.log("🔗 Vinculando alunos às turmas...")
        
        # Agrupar turmas por série (9º Ano A e 9º Ano B são da mesma série)
        turmas_por_serie = {}
        for key, turma in self.turmas_criadas.items():
            # Extrair série do nome (ex: "9º Ano" de "9º Ano A")
            serie = " ".join(turma.nome.split()[:-1]) if len(turma.nome.split()) > 1 else turma.nome
            if serie not in turmas_por_serie:
                turmas_por_serie[serie] = []
            turmas_por_serie[serie].append((key, turma))
        
        # Para cada série, distribuir alunos
        alunos_disponiveis = list(self.alunos_criados)
        random.shuffle(alunos_disponiveis)
        
        aluno_idx = 0
        for serie, turmas_serie in turmas_por_serie.items():
            # Alunos da mesma série estarão em múltiplas matérias
            alunos_serie = alunos_disponiveis[aluno_idx:aluno_idx + alunos_por_turma]
            aluno_idx += alunos_por_turma
            
            if not alunos_serie:
                alunos_serie = random.sample(self.alunos_criados, min(alunos_por_turma, len(self.alunos_criados)))
            
            for aluno in alunos_serie:
                for key, turma in turmas_serie:
                    try:
                        self.storage.vincular_aluno_turma(aluno.id, turma.id)
                        self.stats["vinculos"] += 1
                    except Exception as e:
                        if "já vinculado" in str(e) or "already linked" in str(e) or "duplicate" in str(e).lower():
                            self.log(f"  [skip] Aluno {aluno.id} já vinculado à turma {turma.id}", indent=2)
                        else:
                            raise
        
        self.log(f"[v] {self.stats['vinculos']} vínculos criados", indent=1)
    
    # -----------------------------------------------------------------
    # CRIAÇÃO DE DOCUMENTOS
    # -----------------------------------------------------------------
    
    def criar_documento_texto(self, caminho: Path, conteudo: str, formato: str = "txt"):
        """Cria um arquivo de texto"""
        caminho.parent.mkdir(parents=True, exist_ok=True)
        
        if formato == "json":
            with open(caminho, 'w', encoding='utf-8') as f:
                json.dump(conteudo if isinstance(conteudo, dict) else {"conteudo": conteudo}, f, indent=2, ensure_ascii=False)
        else:
            with open(caminho, 'w', encoding='utf-8') as f:
                f.write(conteudo)
    
    def gerar_enunciado(self, materia: str, turma: str, atividade: str) -> str:
        """Gera conteúdo de enunciado"""
        questoes = QUESTOES_POR_MATERIA.get(materia, QUESTOES_POR_MATERIA["Matemática"])
        
        return ENUNCIADO_EXEMPLO.format(
            materia=materia,
            turma=turma,
            data=datetime.now().strftime("%d/%m/%Y"),
            questao_1=questoes[0] if len(questoes) > 0 else "Questão 1",
            questao_2=questoes[1] if len(questoes) > 1 else "Questão 2",
            questao_3=questoes[2] if len(questoes) > 2 else "Questão 3",
            questao_4=questoes[3] if len(questoes) > 3 else "Questão 4"
        )
    
    def gerar_gabarito(self, materia: str, turma: str, atividade: str) -> str:
        """Gera conteúdo de gabarito"""
        respostas = RESPOSTAS_POR_MATERIA.get(materia, RESPOSTAS_POR_MATERIA["Matemática"])
        
        return GABARITO_EXEMPLO.format(
            atividade=atividade,
            materia=materia,
            turma=turma,
            resp_1=respostas[0] if len(respostas) > 0 else "Resposta 1",
            resp_2=respostas[1] if len(respostas) > 1 else "Resposta 2",
            resp_3=respostas[2] if len(respostas) > 2 else "Resposta 3",
            resp_4=respostas[3] if len(respostas) > 3 else "Resposta 4"
        )
    
    def gerar_prova_aluno(self, materia: str, aluno_nome: str, qualidade: str = "normal") -> str:
        """Gera conteúdo de prova respondida pelo aluno"""
        respostas = RESPOSTAS_POR_MATERIA.get(materia, RESPOSTAS_POR_MATERIA["Matemática"])
        
        if qualidade == "excelente":
            # Respostas corretas
            return f"""Nome: {aluno_nome}

Questão 1: {respostas[0]}
Questão 2: {respostas[1]}
Questão 3: {respostas[2]}
Questão 4: {respostas[3]}
"""
        elif qualidade == "medio":
            # Algumas respostas erradas
            return f"""Nome: {aluno_nome}

Questão 1: {respostas[0]}
Questão 2: Não sei a resposta
Questão 3: {respostas[2]}
Questão 4: Acho que é algo relacionado a {materia.lower()}
"""
        elif qualidade == "ruim":
            # Maioria errada
            return f"""Nome: {aluno_nome}

Questão 1: Não estudei isso
Questão 2: ???
Questão 3: Não lembro
Questão 4: Chutei letra B
"""
        else:
            # Normal - mistura
            return f"""Nome: {aluno_nome}

Questão 1: {respostas[0]}
Questão 2: {random.choice([respostas[1], 'Não sei', 'Deixei em branco'])}
Questão 3: {random.choice([respostas[2], 'Resposta parcial...'])}
Questão 4: {respostas[3] if random.random() > 0.3 else 'Não deu tempo'}
"""
    
    def criar_documentos_base(self, incluir_problemas: bool = True):
        """Cria documentos base (enunciados e gabaritos) para todas as atividades"""
        self.log("📄 Criando documentos base...")
        
        for ativ_key, ativ_info in self.atividades_criadas.items():
            atividade = ativ_info["atividade"]
            materia = ativ_info["materia"]
            turma = ativ_info["turma"]
            
            # Criar enunciado
            try:
                enunciado_conteudo = self.gerar_enunciado(materia, turma, atividade.nome)
                
                # Criar arquivo temporário
                temp_path = Path(tempfile.gettempdir()) / f"enunciado_{atividade.id}.txt"
                self.criar_documento_texto(temp_path, enunciado_conteudo)
                
                doc = self.storage.salvar_documento(
                    arquivo_origem=str(temp_path),
                    tipo=TipoDocumento.ENUNCIADO,
                    atividade_id=atividade.id,
                    criado_por="test_generator"
                )
                
                if doc:
                    self.documentos_criados.append({"tipo": "enunciado", "doc": doc})
                    self.stats["documentos"] += 1
                
                temp_path.unlink(missing_ok=True)
            except Exception as e:
                self.log(f"⚠ Erro ao criar enunciado: {e}", indent=2)
                raise
            
            # Criar gabarito (alguns podem faltar para testar avisos)
            if random.random() > 0.1 or not incluir_problemas:  # 90% têm gabarito
                try:
                    gabarito_conteudo = self.gerar_gabarito(materia, turma, atividade.nome)
                    
                    temp_path = Path(tempfile.gettempdir()) / f"gabarito_{atividade.id}.txt"
                    self.criar_documento_texto(temp_path, gabarito_conteudo)
                    
                    doc = self.storage.salvar_documento(
                        arquivo_origem=str(temp_path),
                        tipo=TipoDocumento.GABARITO,
                        atividade_id=atividade.id,
                        criado_por="test_generator"
                    )
                    
                    if doc:
                        self.documentos_criados.append({"tipo": "gabarito", "doc": doc})
                        self.stats["documentos"] += 1
                    
                    temp_path.unlink(missing_ok=True)
                except Exception as e:
                    self.log(f"⚠ Erro ao criar gabarito: {e}", indent=2)
                    raise
            else:
                self.log(f"  ⚠ Atividade '{atividade.nome}' sem gabarito (teste de aviso)", indent=1)
        
        self.log(f"[v] Documentos base criados", indent=1)
    
    def criar_provas_alunos(self, incluir_problemas: bool = True):
        """Cria provas respondidas pelos alunos"""
        self.log("[>] Criando provas dos alunos...")
        
        for ativ_key, ativ_info in self.atividades_criadas.items():
            atividade = ativ_info["atividade"]
            materia = ativ_info["materia"]
            turma_nome = ativ_info["turma"]
            
            # Encontrar a turma
            turma_key = f"{materia}_{turma_nome}"
            turma = self.turmas_criadas.get(turma_key)
            if not turma:
                continue
            
            # Obter alunos da turma
            alunos_turma = self.storage.listar_alunos(turma.id)
            
            for i, aluno in enumerate(alunos_turma):
                # Determinar qualidade da prova
                qualidade = random.choices(
                    ["excelente", "medio", "normal", "ruim"],
                    weights=[0.2, 0.3, 0.35, 0.15]
                )[0]
                
                # Alguns alunos têm problemas com a prova (para testar avisos)
                problema = None
                if incluir_problemas and random.random() < 0.15:  # 15% com problemas
                    problema = random.choice(list(PROBLEMAS_DOCUMENTO.keys()))
                
                try:
                    if problema:
                        # Criar documento problemático
                        prob_config = PROBLEMAS_DOCUMENTO[problema]
                        conteudo = prob_config["conteudo"]
                        
                        temp_path = Path(tempfile.gettempdir()) / f"prova_{atividade.id}_{aluno.id}.txt"
                        self.criar_documento_texto(temp_path, conteudo)
                        
                        doc = self.storage.salvar_documento(
                            arquivo_origem=str(temp_path),
                            tipo=TipoDocumento.PROVA_RESPONDIDA,
                            atividade_id=atividade.id,
                            aluno_id=aluno.id,
                            criado_por="test_generator"
                        )
                        
                        if doc:
                            # Adicionar metadata do problema
                            self.documentos_criados.append({
                                "tipo": "prova_respondida",
                                "doc": doc,
                                "problema": problema,
                                "problema_descricao": prob_config["descricao"]
                            })
                            self.stats["documentos"] += 1
                            self.stats["documentos_problematicos"] += 1
                            self.log(f"  ⚠ Prova com problema ({problema}): {aluno.nome}", indent=1)
                    else:
                        # Criar prova normal
                        conteudo = self.gerar_prova_aluno(materia, aluno.nome, qualidade)
                        
                        temp_path = Path(tempfile.gettempdir()) / f"prova_{atividade.id}_{aluno.id}.txt"
                        self.criar_documento_texto(temp_path, conteudo)
                        
                        doc = self.storage.salvar_documento(
                            arquivo_origem=str(temp_path),
                            tipo=TipoDocumento.PROVA_RESPONDIDA,
                            atividade_id=atividade.id,
                            aluno_id=aluno.id,
                            criado_por="test_generator"
                        )
                        
                        if doc:
                            self.documentos_criados.append({
                                "tipo": "prova_respondida",
                                "doc": doc,
                                "qualidade": qualidade
                            })
                            self.stats["documentos"] += 1
                    
                    temp_path.unlink(missing_ok=True)
                    
                except Exception as e:
                    self.log(f"⚠ Erro ao criar prova: {e}", indent=2)
                    raise
        
        self.log(f"[v] Provas dos alunos criadas", indent=1)
    
    def criar_documentos_json_exemplo(self):
        """Cria alguns documentos JSON de exemplo (correções, análises)"""
        self.log("🔧 Criando documentos JSON de exemplo...")
        
        # Pegar algumas atividades aleatórias
        atividades_sample = random.sample(
            list(self.atividades_criadas.items()),
            min(3, len(self.atividades_criadas))
        )
        
        for ativ_key, ativ_info in atividades_sample:
            atividade = ativ_info["atividade"]
            turma_key = f"{ativ_info['materia']}_{ativ_info['turma']}"
            turma = self.turmas_criadas.get(turma_key)
            
            if not turma:
                continue
            
            alunos = self.storage.listar_alunos(turma.id)[:2]  # Primeiros 2 alunos
            
            for aluno in alunos:
                # Criar JSON de correção
                correcao_json = {
                    "atividade_id": atividade.id,
                    "aluno_id": aluno.id,
                    "aluno_nome": aluno.nome,
                    "data_correcao": datetime.now().isoformat(),
                    "questoes": [
                        {
                            "numero": 1,
                            "nota": round(random.uniform(0, 2), 1),
                            "nota_maxima": 2.0,
                            "feedback": "Resposta parcialmente correta",
                            "erros": ["Faltou mostrar o cálculo"]
                        },
                        {
                            "numero": 2,
                            "nota": round(random.uniform(0, 2), 1),
                            "nota_maxima": 2.0,
                            "feedback": "Correto",
                            "erros": []
                        },
                        {
                            "numero": 3,
                            "nota": round(random.uniform(0, 3), 1),
                            "nota_maxima": 3.0,
                            "feedback": "Raciocínio correto mas erro de cálculo",
                            "erros": ["Erro aritmético na linha 3"]
                        },
                        {
                            "numero": 4,
                            "nota": round(random.uniform(0, 3), 1),
                            "nota_maxima": 3.0,
                            "feedback": "Boa explicação",
                            "erros": []
                        }
                    ],
                    "nota_total": 0,  # Será calculado
                    "nota_maxima": 10.0,
                    "observacoes": "Aluno demonstra bom entendimento do conteúdo.",
                    "ia_provider": "openai-gpt4o",
                    "ia_modelo": "gpt-4o",
                    "confianca": round(random.uniform(0.85, 0.98), 2)
                }
                
                # Calcular nota total
                correcao_json["nota_total"] = sum(q["nota"] for q in correcao_json["questoes"])
                
                try:
                    temp_path = Path(tempfile.gettempdir()) / f"correcao_{atividade.id}_{aluno.id}.json"
                    self.criar_documento_texto(temp_path, correcao_json, formato="json")
                    
                    doc = self.storage.salvar_documento(
                        arquivo_origem=str(temp_path),
                        tipo=TipoDocumento.CORRECAO,
                        atividade_id=atividade.id,
                        aluno_id=aluno.id,
                        ia_provider="openai-gpt4o",
                        ia_modelo="gpt-4o",
                        criado_por="test_generator"
                    )
                    
                    if doc:
                        self.documentos_criados.append({"tipo": "correcao", "doc": doc})
                        self.stats["documentos"] += 1
                    
                    temp_path.unlink(missing_ok=True)
                except Exception as e:
                    self.log(f"⚠ Erro ao criar correção JSON: {e}", indent=2)
                    raise
        
        self.log(f"[v] Documentos JSON criados", indent=1)
    
    # -----------------------------------------------------------------
    # EXECUÇÃO PRINCIPAL
    # -----------------------------------------------------------------
    
    def gerar_tudo(self,
                   num_alunos: int = 10,
                   alunos_por_turma: int = 5,
                   incluir_problemas: bool = True,
                   materias_config: List[Dict] = None):
        """Gera todos os dados de teste"""
        
        print("\n" + "=" * 60)
        print("[*] GERADOR DE DADOS DE TESTE - PROVA AI")
        print("=" * 60 + "\n")
        
        self.criar_materias(materias_config)
        self.criar_alunos(num_alunos)
        self.vincular_alunos_turmas(alunos_por_turma)
        self.criar_documentos_base(incluir_problemas)
        self.criar_provas_alunos(incluir_problemas)
        self.criar_documentos_json_exemplo()

        # Verificação pós-geração
        print("\n" + "=" * 60)
        print("🔍 VERIFICAÇÃO DOS DOCUMENTOS CRIADOS")
        print("=" * 60)

        doc_types = [
            TipoDocumento.ENUNCIADO,
            TipoDocumento.GABARITO,
            TipoDocumento.PROVA_RESPONDIDA,
            TipoDocumento.CORRECAO
        ]

        counts = {}
        for doc_type in doc_types:
            total = 0
            for ativ_info in self.atividades_criadas.values():
                atividade = ativ_info["atividade"]
                docs = self.storage.listar_documentos(atividade.id, tipo=doc_type)
                total += len(docs)
            counts[doc_type] = total

        print(f"  Verificação: {counts[TipoDocumento.ENUNCIADO]} enunciado(s), "
              f"{counts[TipoDocumento.GABARITO]} gabarito(s), "
              f"{counts[TipoDocumento.PROVA_RESPONDIDA]} prova_respondida(s), "
              f"{counts[TipoDocumento.CORRECAO]} correção(ões)")

        for doc_type in doc_types:
            if counts[doc_type] == 0:
                raise Exception(f"Verification failed: no documents of type '{doc_type.value}' found (count: 0)")

        print("=" * 60 + "\n")

        # Relatório final
        print("\n" + "=" * 60)
        print("📊 RESUMO DOS DADOS CRIADOS")
        print("=" * 60)
        print(f"  [+] Matérias:      {self.stats['materias']}")
        print(f"  [U] Turmas:        {self.stats['turmas']}")
        print(f"  🎓 Alunos:        {self.stats['alunos']}")
        print(f"  🔗 Vínculos:      {self.stats['vinculos']}")
        print(f"  [>] Atividades:    {self.stats['atividades']}")
        print(f"  📄 Documentos:    {self.stats['documentos']}")
        print(f"  ⚠️  Com problemas: {self.stats['documentos_problematicos']}")
        print("=" * 60 + "\n")
        
        if incluir_problemas and self.stats['documentos_problematicos'] > 0:
            print("📋 DOCUMENTOS PROBLEMÁTICOS CRIADOS (para testar avisos):")
            print("-" * 50)
            for doc_info in self.documentos_criados:
                if doc_info.get("problema"):
                    print(f"  • {doc_info['problema']}: {doc_info['problema_descricao']}")
            print()
        
        return self.stats


def limpar_dados_teste(storage: StorageManager):
    """Remove todos os dados do sistema"""
    print("\n⚠️  ATENÇÃO: Isso vai apagar TODOS os dados!")
    confirma = input("Digite 'CONFIRMAR' para continuar: ")
    
    if confirma != "CONFIRMAR":
        print("Operação cancelada.")
        return False
    
    print("\n🗑️  Limpando dados...")
    
    # Limpar banco de dados
    db_path = storage.db_path
    if db_path.exists():
        db_path.unlink()
        print(f"  [v] Banco de dados removido: {db_path}")
    
    # Limpar arquivos
    arquivos_path = storage.arquivos_path
    if arquivos_path.exists():
        shutil.rmtree(arquivos_path)
        print(f"  [v] Arquivos removidos: {arquivos_path}")
    
    # Recriar estrutura
    storage._setup_database()
    arquivos_path.mkdir(parents=True, exist_ok=True)
    
    print("\n[OK] Sistema limpo e pronto para novos dados!\n")
    return True


def limpar_dados_fantasy(storage: StorageManager) -> dict:
    """
    Remove APENAS dados de teste (criado_por='test_generator').
    Preserva dados criados pelo usuario.

    Returns:
        dict com contagem de itens deletados por tipo
    """
    stats = {"materias_deleted": 0, "alunos_deleted": 0}

    # Deletar materias fantasy (cascade deletes turmas, atividades, documentos)
    materias = storage.listar_materias()
    for materia in materias:
        meta = materia.metadata if isinstance(materia.metadata, dict) else {}
        if meta.get("criado_por") == "test_generator":
            storage.deletar_materia(materia.id)
            stats["materias_deleted"] += 1

    # Deletar alunos fantasy
    alunos = storage.listar_alunos()
    for aluno in alunos:
        meta = aluno.metadata if isinstance(aluno.metadata, dict) else {}
        if meta.get("criado_por") == "test_generator":
            storage.deletar_aluno(aluno.id)
            stats["alunos_deleted"] += 1

    return stats


# =================================================================
# MAIN
# =================================================================

def main():
    parser = argparse.ArgumentParser(description="Gerador de dados de teste para Prova AI")
    parser.add_argument("--limpar", action="store_true", help="Limpa todos os dados antes de gerar")
    parser.add_argument("--mini", action="store_true", help="Gera apenas dados mínimos")
    parser.add_argument("--completo", action="store_true", help="Gera dataset completo")
    parser.add_argument("--sem-problemas", action="store_true", help="Não cria documentos problemáticos")
    parser.add_argument("--alunos", type=int, default=20, help="Número de alunos (padrão: 20)")
    
    args = parser.parse_args()
    
    # Usar storage global
    # storage já importado diretamente
    
    # Limpar se solicitado
    if args.limpar:
        if not limpar_dados_teste(storage):
            return
    
    # Configurar geração
    if args.mini:
        config = [{
            "nome": "Matemática",
            "descricao": "Teste mínimo",
            "nivel": NivelEnsino.FUNDAMENTAL_2,
            "turmas": ["9º Ano A"],
            "atividades": [
                {"nome": "Prova Teste", "tipo": "prova", "nota_maxima": 10}
            ]
        }]
        num_alunos = 3
        alunos_por_turma = 3
    elif args.completo:
        config = MATERIAS_CONFIG
        num_alunos = 50
        alunos_por_turma = 15
    else:
        config = MATERIAS_CONFIG_MINI
        num_alunos = args.alunos if args.alunos != 20 else 10
        alunos_por_turma = 5
    
    # Gerar dados
    generator = TestDataGenerator(storage)
    stats = generator.gerar_tudo(
        num_alunos=num_alunos,
        alunos_por_turma=alunos_por_turma,
        incluir_problemas=not args.sem_problemas,
        materias_config=config
    )
    
    print("[OK] Dados de teste criados com sucesso!")
    print("\nPróximos passos:")
    print("  1. Inicie o servidor: python -m uvicorn main_v2:app --reload")
    print("  2. Acesse: http://localhost:8000")
    print("  3. Explore as matérias, turmas e documentos criados")
    print("  4. Teste o chat com diferentes filtros de contexto")
    print()


if __name__ == "__main__":
    main()
