"""
Supabase Storage Client para Prova AI

Gerencia upload/download de arquivos no Supabase Storage.
Usa variáveis de ambiente para credenciais (seguro para produção).

Configuração:
    SUPABASE_URL=https://xxxxx.supabase.co
    SUPABASE_SERVICE_KEY=eyJ...
    SUPABASE_BUCKET=documentos
"""

import os
import httpx
from pathlib import Path
from typing import Optional, Tuple
from dotenv import load_dotenv

load_dotenv()


class SupabaseStorage:
    """Cliente para Supabase Storage"""

    def __init__(self):
        self.url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self.key = os.getenv("SUPABASE_SERVICE_KEY", "")
        self.bucket = os.getenv("SUPABASE_BUCKET", "documentos")

        self._enabled = bool(self.url and self.key)

        if self._enabled:
            self.storage_url = f"{self.url}/storage/v1"
            self.headers = {
                "apikey": self.key,
                "Authorization": f"Bearer {self.key}",
            }
            print(f"[Supabase] Storage habilitado: {self.url}")
        else:
            print("[Supabase] Storage DESABILITADO (credenciais não configuradas)")

    @property
    def enabled(self) -> bool:
        """Retorna True se o Supabase está configurado"""
        return self._enabled

    def upload(self, local_path: str, remote_path: str) -> Tuple[bool, str]:
        """
        Faz upload de arquivo para Supabase Storage.

        Args:
            local_path: Caminho local do arquivo
            remote_path: Caminho no bucket (ex: "materia_id/turma_id/atividade_id/arquivo.pdf")

        Returns:
            Tuple[success: bool, message: str]
        """
        if not self._enabled:
            return False, "Supabase não configurado"

        file_path = Path(local_path)
        if not file_path.exists():
            return False, f"Arquivo não encontrado: {local_path}"

        # Detectar content-type
        ext = file_path.suffix.lower()
        content_types = {
            ".pdf": "application/pdf",
            ".json": "application/json",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
        content_type = content_types.get(ext, "application/octet-stream")

        # Normalizar path (remover barras iniciais, usar /)
        remote_path = remote_path.replace("\\", "/").lstrip("/")

        url = f"{self.storage_url}/object/{self.bucket}/{remote_path}"

        try:
            with open(local_path, "rb") as f:
                content = f.read()

            headers = {
                **self.headers,
                "Content-Type": content_type,
                "x-upsert": "true",  # Sobrescreve se existir
            }

            with httpx.Client(timeout=60) as client:
                response = client.post(url, headers=headers, content=content)

            if response.status_code in (200, 201):
                return True, f"Upload OK: {remote_path}"
            else:
                return False, f"Erro {response.status_code}: {response.text}"

        except Exception as e:
            return False, f"Erro no upload: {str(e)}"

    def download(self, remote_path: str, local_path: str) -> Tuple[bool, str]:
        """
        Faz download de arquivo do Supabase Storage.

        Args:
            remote_path: Caminho no bucket
            local_path: Caminho local para salvar

        Returns:
            Tuple[success: bool, message: str]
        """
        if not self._enabled:
            return False, "Supabase não configurado"

        # Normalizar path
        remote_path = remote_path.replace("\\", "/").lstrip("/")

        url = f"{self.storage_url}/object/{self.bucket}/{remote_path}"

        try:
            with httpx.Client(timeout=60) as client:
                response = client.get(url, headers=self.headers)

            if response.status_code == 200:
                # Criar diretório se não existir
                Path(local_path).parent.mkdir(parents=True, exist_ok=True)

                with open(local_path, "wb") as f:
                    f.write(response.content)

                return True, f"Download OK: {local_path}"
            elif response.status_code == 404:
                return False, f"Arquivo não encontrado: {remote_path}"
            else:
                return False, f"Erro {response.status_code}: {response.text}"

        except Exception as e:
            return False, f"Erro no download: {str(e)}"

    def exists(self, remote_path: str) -> bool:
        """Verifica se arquivo existe no bucket"""
        if not self._enabled:
            return False

        remote_path = remote_path.replace("\\", "/").lstrip("/")
        url = f"{self.storage_url}/object/{self.bucket}/{remote_path}"

        try:
            with httpx.Client(timeout=10) as client:
                response = client.head(url, headers=self.headers)
            return response.status_code == 200
        except:
            return False

    def delete(self, remote_path: str) -> Tuple[bool, str]:
        """Deleta arquivo do bucket"""
        if not self._enabled:
            return False, "Supabase não configurado"

        remote_path = remote_path.replace("\\", "/").lstrip("/")
        url = f"{self.storage_url}/object/{self.bucket}"

        try:
            with httpx.Client(timeout=30) as client:
                response = client.request(
                    "DELETE",
                    url,
                    headers=self.headers,
                    json={"prefixes": [remote_path]}
                )

            if response.status_code in (200, 204):
                return True, f"Deletado: {remote_path}"
            else:
                return False, f"Erro {response.status_code}: {response.text}"

        except Exception as e:
            return False, f"Erro ao deletar: {str(e)}"

    def get_public_url(self, remote_path: str) -> Optional[str]:
        """Retorna URL pública do arquivo (se bucket for público)"""
        if not self._enabled:
            return None

        remote_path = remote_path.replace("\\", "/").lstrip("/")
        return f"{self.storage_url}/object/public/{self.bucket}/{remote_path}"

    def get_signed_url(self, remote_path: str, expires_in: int = 3600) -> Optional[str]:
        """
        Gera URL assinada temporária para download.

        Args:
            remote_path: Caminho no bucket
            expires_in: Tempo de expiração em segundos (default: 1 hora)

        Returns:
            URL assinada ou None se falhar
        """
        if not self._enabled:
            return None

        remote_path = remote_path.replace("\\", "/").lstrip("/")
        url = f"{self.storage_url}/object/sign/{self.bucket}/{remote_path}"

        try:
            with httpx.Client(timeout=10) as client:
                response = client.post(
                    url,
                    headers=self.headers,
                    json={"expiresIn": expires_in}
                )

            if response.status_code == 200:
                data = response.json()
                signed_url = data.get("signedURL", "")
                if signed_url:
                    return f"{self.url}/storage/v1{signed_url}"
            return None

        except:
            return None


# Instância global
supabase_storage = SupabaseStorage()
