"""
Testes para o comportamento de UPSERT do seeding de prompts padrão.

Verifica que _seed_prompts_padrao() ATUALIZA prompts existentes no SQLite
com texto_sistema e texto do PROMPTS_PADRAO — não apenas insere quando ausentes.

Problema central: quando o servidor já rodou antes (prompts no DB), um simples
restart após atualizar PROMPTS_PADRAO não chegava ao DB porque o método só faz
INSERT IF NOT EXISTS.

Relacionado ao plano: docs/PLAN_Pipeline_Relatorios_Qualidade.md
Tasks: F3-T3, F4-T3, F5-T3
"""

import sqlite3
import pytest


class TestSeedingAtualizaPromptsExistentes:
    """
    F3-T3, F4-T3, F5-T3: _seed_prompts_padrao() deve atualizar prompts
    já existentes no banco SQLite com o conteúdo atual de PROMPTS_PADRAO.

    Cenário crítico: servidor já rodou antes de F3-T2/F4-T2/F5-T2 (prompts
    padrão estão no DB). Após atualizar o código com novos prompts, o servidor
    faz restart — _seed_prompts_padrao() deve detectar que texto_sistema mudou
    e atualizar o DB.
    """

    def _zerar_texto_sistema(self, db_path: str, prompt_id: str):
        """Helper: zera texto_sistema de um prompt no DB para simular versão antiga."""
        conn = sqlite3.connect(db_path)
        conn.execute("UPDATE prompts SET texto_sistema = NULL WHERE id = ?", (prompt_id,))
        conn.commit()
        conn.close()

    def _get_texto_sistema(self, db_path: str, prompt_id: str):
        """Helper: retorna texto_sistema atual de um prompt no DB."""
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT texto_sistema FROM prompts WHERE id = ?", (prompt_id,)
        ).fetchone()
        conn.close()
        return row["texto_sistema"] if row else None

    def test_seed_atualiza_texto_sistema_corrigir(self, tmp_path):
        """
        F3-T3: Re-seeding deve atualizar texto_sistema do CORRIGIR
        mesmo se o prompt já existia no DB com valor antigo (NULL).
        """
        from prompts import PromptManager

        db_path = str(tmp_path / "test_f3t3.db")

        # Passo 1: Criar DB inicial (simula deploy antigo, antes de F3-T2)
        PromptManager(db_path=db_path)

        # Passo 2: Simular prompt antigo — zerar texto_sistema (antes de F3-T2 não havia)
        self._zerar_texto_sistema(db_path, "default_corrigir")
        assert self._get_texto_sistema(db_path, "default_corrigir") is None, (
            "Setup falhou: texto_sistema deveria ser NULL antes do re-seeding"
        )

        # Passo 3: Re-inicializar PromptManager (simula restart do servidor após deploy de F3-T2)
        PromptManager(db_path=db_path)

        # Assert: texto_sistema deve ter sido restaurado do PROMPTS_PADRAO
        texto_sistema = self._get_texto_sistema(db_path, "default_corrigir")
        assert texto_sistema is not None, (
            "_seed_prompts_padrao() não atualizou texto_sistema do CORRIGIR. "
            "O método deve fazer UPSERT — não apenas INSERT quando não existe. "
            "Isso garante que deploys existentes recebam os novos prompts após restart."
        )
        assert len(texto_sistema) > 100, (
            f"texto_sistema atualizado é muito curto ({len(texto_sistema)} chars). "
            "Esperado o prompt pedagógico completo do PROMPTS_PADRAO."
        )

    def test_seed_atualiza_texto_sistema_analisar_habilidades(self, tmp_path):
        """
        F4-T3: Re-seeding deve atualizar texto_sistema do ANALISAR_HABILIDADES
        mesmo se o prompt já existia no DB com valor antigo (NULL).
        """
        from prompts import PromptManager

        db_path = str(tmp_path / "test_f4t3.db")

        PromptManager(db_path=db_path)
        self._zerar_texto_sistema(db_path, "default_analisar_habilidades")
        assert self._get_texto_sistema(db_path, "default_analisar_habilidades") is None

        # Re-seed (servidor restart)
        PromptManager(db_path=db_path)

        texto_sistema = self._get_texto_sistema(db_path, "default_analisar_habilidades")
        assert texto_sistema is not None, (
            "_seed_prompts_padrao() não atualizou texto_sistema do ANALISAR_HABILIDADES. "
            "O seeding deve UPSERT: quando o prompt já existe, atualizar texto_sistema."
        )
        assert len(texto_sistema) > 100, (
            f"texto_sistema do ANALISAR_HABILIDADES muito curto ({len(texto_sistema)} chars)"
        )

    def test_seed_atualiza_texto_sistema_gerar_relatorio(self, tmp_path):
        """
        F5-T3: Re-seeding deve atualizar texto_sistema do GERAR_RELATORIO
        mesmo se o prompt já existia no DB com valor antigo (NULL).
        """
        from prompts import PromptManager

        db_path = str(tmp_path / "test_f5t3.db")

        PromptManager(db_path=db_path)
        self._zerar_texto_sistema(db_path, "default_gerar_relatorio")
        assert self._get_texto_sistema(db_path, "default_gerar_relatorio") is None

        # Re-seed
        PromptManager(db_path=db_path)

        texto_sistema = self._get_texto_sistema(db_path, "default_gerar_relatorio")
        assert texto_sistema is not None, (
            "_seed_prompts_padrao() não atualizou texto_sistema do GERAR_RELATORIO. "
            "O relatório holístico depende do texto_sistema para instruir o autor de relatório."
        )
        assert len(texto_sistema) > 100, (
            f"texto_sistema do GERAR_RELATORIO muito curto ({len(texto_sistema)} chars)"
        )

    def test_seed_atualiza_texto_principal_corrigir(self, tmp_path):
        """
        Seeding deve também atualizar o campo texto (prompt principal) quando
        o prompt já existe com versão antiga — garante que o corpo do prompt
        também seja atualizado, não só o texto_sistema.
        """
        from prompts import PromptManager, PROMPTS_PADRAO, EtapaProcessamento

        db_path = str(tmp_path / "test_texto_principal.db")

        # Criar DB com prompts iniciais
        PromptManager(db_path=db_path)

        # Simular versão antiga: texto antigo no DB
        old_texto = "Texto antigo sem narrativa_correcao"
        conn = sqlite3.connect(db_path)
        conn.execute(
            "UPDATE prompts SET texto = ? WHERE id = 'default_corrigir'",
            (old_texto,)
        )
        conn.commit()
        conn.close()

        # Re-seed
        PromptManager(db_path=db_path)

        # Assert: texto deve ter sido atualizado com o conteúdo atual de PROMPTS_PADRAO
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT texto FROM prompts WHERE id = 'default_corrigir'"
        ).fetchone()
        conn.close()

        texto_novo = row["texto"]
        expected = PROMPTS_PADRAO[EtapaProcessamento.CORRIGIR].texto

        assert texto_novo == expected, (
            "Após re-seeding, o campo 'texto' do CORRIGIR não foi atualizado. "
            "O UPSERT deve sincronizar tanto texto_sistema quanto texto do PROMPTS_PADRAO."
        )
        assert "narrativa_correcao" in texto_novo, (
            "Campo 'narrativa_correcao' ausente no texto atualizado — "
            "o seeding não aplicou o prompt narrativo da F3-T2."
        )

    def test_seed_preserva_prompt_customizado_nao_padrao(self, tmp_path):
        """
        Seeding deve preservar prompts customizados (não presentes em PROMPTS_PADRAO)
        sem alterá-los — o UPSERT só deve tocar os IDs de PROMPTS_PADRAO.
        """
        from prompts import PromptManager, EtapaProcessamento

        db_path = str(tmp_path / "test_preserva.db")
        manager = PromptManager(db_path=db_path)

        # Criar prompt customizado (ID único, não em PROMPTS_PADRAO)
        prompt_custom = manager.criar_prompt(
            nome="Meu Prompt Personalizado",
            etapa=EtapaProcessamento.CORRIGIR,
            texto="Correção personalizada do professor — não alterar no seeding",
        )
        custom_id = prompt_custom.id

        # Re-seed
        PromptManager(db_path=db_path)

        # Verificar que o prompt customizado não foi alterado
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT texto FROM prompts WHERE id = ?", (custom_id,)
        ).fetchone()
        conn.close()

        assert row is not None, "Prompt customizado foi deletado pelo seeding — bug crítico"
        assert row["texto"] == "Correção personalizada do professor — não alterar no seeding", (
            "Prompt customizado foi modificado pelo re-seeding. "
            "O seeding deve tocar apenas os IDs presentes em PROMPTS_PADRAO."
        )
