-- =================================================================
-- PROVA AI - PostgreSQL Schema Migration
-- =================================================================
-- Run this in Supabase SQL Editor to create all required tables.
-- This replaces the SQLite schema.
-- =================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =================================================================
-- TABLE: materias
-- =================================================================
CREATE TABLE IF NOT EXISTS materias (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    descricao TEXT,
    nivel TEXT DEFAULT 'outro',
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- =================================================================
-- TABLE: turmas
-- =================================================================
CREATE TABLE IF NOT EXISTS turmas (
    id TEXT PRIMARY KEY,
    materia_id TEXT NOT NULL REFERENCES materias(id) ON DELETE CASCADE,
    nome TEXT NOT NULL,
    ano_letivo INTEGER,
    periodo TEXT,
    descricao TEXT,
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_turmas_materia ON turmas(materia_id);

-- =================================================================
-- TABLE: alunos
-- =================================================================
CREATE TABLE IF NOT EXISTS alunos (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    email TEXT,
    matricula TEXT,
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- =================================================================
-- TABLE: alunos_turmas (many-to-many)
-- =================================================================
CREATE TABLE IF NOT EXISTS alunos_turmas (
    id TEXT PRIMARY KEY,
    aluno_id TEXT NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
    turma_id TEXT NOT NULL REFERENCES turmas(id) ON DELETE CASCADE,
    ativo BOOLEAN DEFAULT TRUE,
    data_entrada TIMESTAMPTZ DEFAULT NOW(),
    data_saida TIMESTAMPTZ,
    observacoes TEXT,
    UNIQUE(aluno_id, turma_id)
);

CREATE INDEX IF NOT EXISTS idx_alunos_turmas_aluno ON alunos_turmas(aluno_id);
CREATE INDEX IF NOT EXISTS idx_alunos_turmas_turma ON alunos_turmas(turma_id);

-- =================================================================
-- TABLE: atividades
-- =================================================================
CREATE TABLE IF NOT EXISTS atividades (
    id TEXT PRIMARY KEY,
    turma_id TEXT NOT NULL REFERENCES turmas(id) ON DELETE CASCADE,
    nome TEXT NOT NULL,
    tipo TEXT,
    data_aplicacao TIMESTAMPTZ,
    data_entrega TIMESTAMPTZ,
    peso REAL DEFAULT 1.0,
    nota_maxima REAL DEFAULT 10.0,
    descricao TEXT,
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_atividades_turma ON atividades(turma_id);

-- =================================================================
-- TABLE: documentos
-- =================================================================
CREATE TABLE IF NOT EXISTS documentos (
    id TEXT PRIMARY KEY,
    tipo TEXT NOT NULL,
    atividade_id TEXT NOT NULL REFERENCES atividades(id) ON DELETE CASCADE,
    aluno_id TEXT REFERENCES alunos(id) ON DELETE SET NULL,
    display_name TEXT DEFAULT '',
    nome_arquivo TEXT,
    caminho_arquivo TEXT,
    extensao TEXT,
    tamanho_bytes INTEGER DEFAULT 0,
    ia_provider TEXT,
    ia_modelo TEXT,
    prompt_usado TEXT,
    prompt_versao TEXT,
    tokens_usados INTEGER DEFAULT 0,
    tempo_processamento_ms REAL DEFAULT 0,
    status TEXT DEFAULT 'concluido',
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW(),
    criado_por TEXT,
    versao INTEGER DEFAULT 1,
    documento_origem_id TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_documentos_atividade ON documentos(atividade_id);
CREATE INDEX IF NOT EXISTS idx_documentos_aluno ON documentos(aluno_id);

-- =================================================================
-- TABLE: resultados
-- =================================================================
CREATE TABLE IF NOT EXISTS resultados (
    id TEXT PRIMARY KEY,
    aluno_id TEXT NOT NULL REFERENCES alunos(id) ON DELETE CASCADE,
    atividade_id TEXT NOT NULL REFERENCES atividades(id) ON DELETE CASCADE,
    nota_obtida REAL,
    nota_maxima REAL DEFAULT 10.0,
    percentual REAL,
    total_questoes INTEGER DEFAULT 0,
    questoes_corretas INTEGER DEFAULT 0,
    questoes_parciais INTEGER DEFAULT 0,
    questoes_incorretas INTEGER DEFAULT 0,
    habilidades_demonstradas TEXT,
    habilidades_faltantes TEXT,
    feedback_geral TEXT,
    corrigido_em TIMESTAMPTZ,
    corrigido_por_ia TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    UNIQUE(aluno_id, atividade_id)
);

-- =================================================================
-- TABLE: prompts
-- =================================================================
CREATE TABLE IF NOT EXISTS prompts (
    id TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    etapa TEXT NOT NULL,
    texto TEXT NOT NULL,
    texto_sistema TEXT,
    descricao TEXT,
    is_padrao BOOLEAN DEFAULT FALSE,
    is_ativo BOOLEAN DEFAULT TRUE,
    materia_id TEXT,
    variaveis JSONB DEFAULT '[]'::jsonb,
    versao INTEGER DEFAULT 1,
    criado_em TIMESTAMPTZ DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ DEFAULT NOW(),
    criado_por TEXT
);

-- =================================================================
-- TABLE: prompts_historico
-- =================================================================
CREATE TABLE IF NOT EXISTS prompts_historico (
    id SERIAL PRIMARY KEY,
    prompt_id TEXT NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
    versao INTEGER NOT NULL,
    texto TEXT NOT NULL,
    modificado_em TIMESTAMPTZ DEFAULT NOW(),
    modificado_por TEXT
);

-- =================================================================
-- MIGRATIONS: Add columns to existing tables
-- =================================================================
-- Safe to re-run: IF NOT EXISTS prevents errors on already-migrated DBs.

ALTER TABLE documentos ADD COLUMN IF NOT EXISTS display_name TEXT DEFAULT '';

-- =================================================================
-- Row Level Security (RLS) - Disable for now (service key bypasses)
-- =================================================================
-- Enable RLS if you need per-user security later
-- ALTER TABLE materias ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE turmas ENABLE ROW LEVEL SECURITY;
-- etc.

-- =================================================================
-- DONE
-- =================================================================
-- After running this:
-- 1. Set DATABASE_URL or ensure SUPABASE_URL is configured
-- 2. Deploy the updated backend code
-- 3. Data will persist between deployments!
