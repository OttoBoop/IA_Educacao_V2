"""
Supabase PostgreSQL Database Client for Prova AI

Uses the Supabase Python client for database operations.
Replaces SQLite with persistent PostgreSQL storage.

Configuration:
    SUPABASE_URL=https://xxxxx.supabase.co
    SUPABASE_SERVICE_KEY=eyJ...
"""

import os
import json
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Try to import supabase client
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("[SupabaseDB] supabase-py not installed. Run: pip install supabase")


class SupabaseDB:
    """
    Supabase PostgreSQL client using PostgREST API.

    Provides CRUD operations for all tables with automatic
    JSON serialization for metadata fields.
    """

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self.key = os.getenv("SUPABASE_SERVICE_KEY", "")

        self._client: Optional[Client] = None
        self._enabled = False

        if SUPABASE_AVAILABLE and self.url and self.key:
            try:
                self._client = create_client(self.url, self.key)
                self._enabled = True
                print(f"[SupabaseDB] Connected to PostgreSQL: {self.url}")
            except Exception as e:
                print(f"[SupabaseDB] Failed to connect: {e}")
        else:
            if not SUPABASE_AVAILABLE:
                print("[SupabaseDB] supabase-py not installed")
            elif not self.url or not self.key:
                print("[SupabaseDB] Credentials not configured")

    @property
    def enabled(self) -> bool:
        """Returns True if PostgreSQL connection is available"""
        return self._enabled

    @property
    def client(self) -> Optional[Client]:
        """Returns the Supabase client"""
        return self._client

    # ============================================================
    # GENERIC CRUD OPERATIONS
    # ============================================================

    def insert(self, table: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Insert a row into a table"""
        if not self._enabled:
            return None

        try:
            # Convert datetime objects to ISO strings
            data = self._serialize_data(data)

            result = self._client.table(table).insert(data).execute()

            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
        except Exception as e:
            print(f"[SupabaseDB] Insert error in {table}: {e}")
            return None

    def select(self, table: str, filters: Dict[str, Any] = None,
               order_by: str = None, order_desc: bool = False,
               limit: int = None) -> List[Dict[str, Any]]:
        """Select rows from a table with optional filters"""
        if not self._enabled:
            return []

        try:
            query = self._client.table(table).select("*")

            if filters:
                for key, value in filters.items():
                    if value is None:
                        query = query.is_(key, "null")
                    else:
                        query = query.eq(key, value)

            if order_by:
                query = query.order(order_by, desc=order_desc)

            if limit:
                query = query.limit(limit)

            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"[SupabaseDB] Select error in {table}: {e}")
            return []

    def select_one(self, table: str, id: str) -> Optional[Dict[str, Any]]:
        """Select a single row by ID"""
        if not self._enabled:
            return None

        try:
            result = self._client.table(table).select("*").eq("id", id).limit(1).execute()

            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
        except Exception as e:
            print(f"[SupabaseDB] Select one error in {table}: {e}")
            return None

    def update(self, table: str, id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a row by ID"""
        if not self._enabled:
            return None

        try:
            data = self._serialize_data(data)
            data["atualizado_em"] = datetime.now().isoformat()

            result = self._client.table(table).update(data).eq("id", id).execute()

            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
        except Exception as e:
            print(f"[SupabaseDB] Update error in {table}: {e}")
            return None

    def delete(self, table: str, id: str) -> bool:
        """Delete a row by ID"""
        if not self._enabled:
            return False

        try:
            result = self._client.table(table).delete().eq("id", id).execute()
            return True
        except Exception as e:
            print(f"[SupabaseDB] Delete error in {table}: {e}")
            return False

    def delete_where(self, table: str, filters: Dict[str, Any]) -> int:
        """Delete rows matching filters"""
        if not self._enabled:
            return 0

        try:
            query = self._client.table(table).delete()

            for key, value in filters.items():
                if value is None:
                    query = query.is_(key, "null")
                else:
                    query = query.eq(key, value)

            result = query.execute()
            return len(result.data) if result.data else 0
        except Exception as e:
            print(f"[SupabaseDB] Delete where error in {table}: {e}")
            return 0

    def count(self, table: str, filters: Dict[str, Any] = None) -> int:
        """Count rows in a table"""
        if not self._enabled:
            return 0

        try:
            query = self._client.table(table).select("id", count="exact")

            if filters:
                for key, value in filters.items():
                    if value is None:
                        query = query.is_(key, "null")
                    else:
                        query = query.eq(key, value)

            result = query.execute()
            return result.count if result.count else 0
        except Exception as e:
            print(f"[SupabaseDB] Count error in {table}: {e}")
            return 0

    def execute_sql(self, sql: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute raw SQL (via RPC function)"""
        if not self._enabled:
            return []

        # Note: Raw SQL requires an RPC function in Supabase
        # For complex queries, consider creating views or functions
        print(f"[SupabaseDB] Warning: execute_sql not fully supported yet")
        return []

    # ============================================================
    # SPECIALIZED QUERIES
    # ============================================================

    def select_with_join(self, table: str, join_table: str,
                         join_column: str, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Select with a simple join (uses Supabase nested selects)"""
        if not self._enabled:
            return []

        try:
            # Supabase uses nested select for joins
            select_query = f"*, {join_table}(*)"
            query = self._client.table(table).select(select_query)

            if filters:
                for key, value in filters.items():
                    if value is None:
                        query = query.is_(key, "null")
                    else:
                        query = query.eq(key, value)

            result = query.execute()
            return result.data if result.data else []
        except Exception as e:
            print(f"[SupabaseDB] Join query error: {e}")
            return []

    def upsert(self, table: str, data: Dict[str, Any], on_conflict: str = "id") -> Optional[Dict[str, Any]]:
        """Insert or update a row"""
        if not self._enabled:
            return None

        try:
            data = self._serialize_data(data)

            result = self._client.table(table).upsert(data, on_conflict=on_conflict).execute()

            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
        except Exception as e:
            print(f"[SupabaseDB] Upsert error in {table}: {e}")
            return None

    # ============================================================
    # HELPERS
    # ============================================================

    def _serialize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert Python objects to JSON-serializable format"""
        result = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            elif isinstance(value, dict):
                # Already a dict, will be stored as JSONB
                result[key] = value
            elif isinstance(value, list):
                result[key] = value
            elif hasattr(value, 'value'):
                # Enum
                result[key] = value.value
            else:
                result[key] = value
        return result

    def test_connection(self) -> Tuple[bool, str]:
        """Test database connection"""
        if not self._enabled:
            return False, "Database not configured"

        try:
            # Try to count materias
            result = self._client.table("materias").select("id", count="exact").limit(1).execute()
            return True, f"Connected! {result.count} materias in database"
        except Exception as e:
            return False, f"Connection failed: {e}"


# Global instance
supabase_db = SupabaseDB()
