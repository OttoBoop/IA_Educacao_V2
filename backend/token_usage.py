"""
Persistent token usage records for NOVO CR.

Document metadata is enough when an AI run creates artifacts. When a run spends
tokens and fails before saving any document, this module records the cost event
without inventing a Documento.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from storage import storage

try:
    from supabase_db import supabase_db
    SUPABASE_TOKEN_USAGE_AVAILABLE = supabase_db.enabled
except Exception:
    supabase_db = None
    SUPABASE_TOKEN_USAGE_AVAILABLE = False


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TokenUsageRecord:
    id: str
    cost_run_id: str
    atividade_id: Optional[str]
    aluno_id: Optional[str]
    etapa: str
    provider: str
    modelo: str
    tokens_entrada: int
    tokens_saida: int
    status: str
    erro: Optional[str] = None
    erro_codigo: Optional[int] = None
    retryable: bool = False
    tentativas: int = 1
    tempo_ms: float = 0
    prompt_id: Optional[str] = None
    source: str = "executor"
    metadata: Dict[str, Any] = field(default_factory=dict)
    criado_em: str = field(default_factory=_utc_now_iso)

    @property
    def tokens_total(self) -> int:
        return int(self.tokens_entrada or 0) + int(self.tokens_saida or 0)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["tokens_total"] = self.tokens_total
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TokenUsageRecord":
        return cls(
            id=data["id"],
            cost_run_id=data["cost_run_id"],
            atividade_id=data.get("atividade_id"),
            aluno_id=data.get("aluno_id"),
            etapa=data.get("etapa") or "unknown",
            provider=data.get("provider") or "",
            modelo=data.get("modelo") or "",
            tokens_entrada=int(data.get("tokens_entrada") or 0),
            tokens_saida=int(data.get("tokens_saida") or 0),
            status=data.get("status") or "erro",
            erro=data.get("erro"),
            erro_codigo=data.get("erro_codigo"),
            retryable=bool(data.get("retryable", False)),
            tentativas=int(data.get("tentativas") or 1),
            tempo_ms=float(data.get("tempo_ms") or 0),
            prompt_id=data.get("prompt_id"),
            source=data.get("source") or "executor",
            metadata=data.get("metadata") if isinstance(data.get("metadata"), dict) else {},
            criado_em=data.get("criado_em") or _utc_now_iso(),
        )


class TokenUsageStore:
    def __init__(self, base_path: Optional[Path] = None, use_supabase: Optional[bool] = None):
        self.base_path = Path(base_path) if base_path is not None else storage.base_path
        self.usage_path = self.base_path / "token_usage"
        self.use_supabase = SUPABASE_TOKEN_USAGE_AVAILABLE if use_supabase is None else use_supabase

    def _path_for(self, created_at: Optional[str] = None) -> Path:
        date_text = created_at or _utc_now_iso()
        month = date_text[:7]
        return self.usage_path / f"{month}.json"

    def add(self, record: TokenUsageRecord) -> TokenUsageRecord:
        if self.use_supabase and supabase_db is not None:
            try:
                inserted = supabase_db.insert("token_usage", record.to_dict())
                if inserted:
                    return record
            except Exception:
                # Fall back to the local monthly file. The endpoint will still
                # expose the record, but docs must keep this limitation visible.
                pass

        self.usage_path.mkdir(parents=True, exist_ok=True)
        path = self._path_for(record.criado_em)
        records = [item.to_dict() for item in self._read_file(path)]
        records.append(record.to_dict())
        tmp_path = path.with_suffix(".json.tmp")
        tmp_path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp_path.replace(path)
        return record

    def list_records(self, limit: Optional[int] = None) -> List[TokenUsageRecord]:
        records_by_id: Dict[str, TokenUsageRecord] = {}
        if self.use_supabase and supabase_db is not None:
            for row in supabase_db.select(
                "token_usage",
                order_by="criado_em",
                order_desc=True,
                limit=limit,
            ):
                try:
                    record = TokenUsageRecord.from_dict(row)
                except Exception:
                    continue
                records_by_id[record.id] = record

        if not self.usage_path.exists():
            records = list(records_by_id.values())
            return sorted(records, key=lambda item: item.criado_em, reverse=True)[:limit]

        for path in sorted(self.usage_path.glob("*.json"), reverse=True):
            for record in self._read_file(path):
                records_by_id.setdefault(record.id, record)
            if limit is not None and len(records_by_id) >= limit:
                break

        records = sorted(records_by_id.values(), key=lambda item: item.criado_em, reverse=True)
        return records[:limit] if limit is not None else records

    def _read_file(self, path: Path) -> List[TokenUsageRecord]:
        if not path.exists():
            return []
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"Token usage file must contain a list: {path}")
        return [TokenUsageRecord.from_dict(item) for item in data if isinstance(item, dict)]


token_usage_store = TokenUsageStore()


def record_token_usage(
    *,
    cost_run_id: str,
    atividade_id: Optional[str],
    aluno_id: Optional[str],
    etapa: str,
    provider: str,
    modelo: str,
    tokens_entrada: int,
    tokens_saida: int,
    status: str,
    erro: Optional[str] = None,
    erro_codigo: Optional[int] = None,
    retryable: bool = False,
    tentativas: int = 1,
    tempo_ms: float = 0,
    prompt_id: Optional[str] = None,
    source: str = "executor",
    metadata: Optional[Dict[str, Any]] = None,
) -> TokenUsageRecord:
    record = TokenUsageRecord(
        id=f"usage_{uuid.uuid4().hex[:16]}",
        cost_run_id=cost_run_id,
        atividade_id=atividade_id,
        aluno_id=aluno_id,
        etapa=etapa,
        provider=provider,
        modelo=modelo,
        tokens_entrada=int(tokens_entrada or 0),
        tokens_saida=int(tokens_saida or 0),
        status=status,
        erro=erro,
        erro_codigo=erro_codigo,
        retryable=retryable,
        tentativas=tentativas,
        tempo_ms=float(tempo_ms or 0),
        prompt_id=prompt_id,
        source=source,
        metadata=metadata or {},
    )
    return token_usage_store.add(record)
