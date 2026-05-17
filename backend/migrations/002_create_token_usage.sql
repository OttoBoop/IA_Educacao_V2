-- =================================================================
-- NOVO CR - Token usage persistence
-- =================================================================
-- Run this in Supabase SQL Editor when /api/custos/status reports:
--   token_usage_backend.supabase.table_available = false
--   PGRST205 / public.token_usage missing from schema cache
--
-- Safe to re-run.
-- =================================================================

CREATE TABLE IF NOT EXISTS token_usage (
    id TEXT PRIMARY KEY,
    cost_run_id TEXT NOT NULL,
    atividade_id TEXT,
    aluno_id TEXT,
    etapa TEXT NOT NULL,
    provider TEXT NOT NULL,
    modelo TEXT NOT NULL,
    tokens_entrada INTEGER DEFAULT 0,
    tokens_saida INTEGER DEFAULT 0,
    tokens_total INTEGER DEFAULT 0,
    status TEXT NOT NULL,
    erro TEXT,
    erro_codigo INTEGER,
    retryable BOOLEAN DEFAULT FALSE,
    tentativas INTEGER DEFAULT 1,
    tempo_ms REAL DEFAULT 0,
    prompt_id TEXT,
    source TEXT DEFAULT 'executor',
    metadata JSONB DEFAULT '{}'::jsonb,
    criado_em TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_token_usage_cost_run ON token_usage(cost_run_id);
CREATE INDEX IF NOT EXISTS idx_token_usage_atividade ON token_usage(atividade_id);
CREATE INDEX IF NOT EXISTS idx_token_usage_aluno ON token_usage(aluno_id);
CREATE INDEX IF NOT EXISTS idx_token_usage_criado_em ON token_usage(criado_em);

-- Keep token usage private to the service role. The backend uses the
-- SUPABASE_SERVICE_KEY, which bypasses RLS; public anon clients should not read
-- this operational cost table directly.
ALTER TABLE token_usage ENABLE ROW LEVEL SECURITY;

-- Ask PostgREST to refresh the schema cache so /api/custos/status can stop
-- reporting PGRST205 shortly after the migration is applied.
NOTIFY pgrst, 'reload schema';
