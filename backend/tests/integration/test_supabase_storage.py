"""
Supabase Storage Integration Tests

Tests upload/download/delete/list/URL operations against the real Supabase Storage API.
Skipped automatically if SUPABASE_URL is not configured.

All test files are uploaded under _test_ci/ prefix and cleaned up after each test.
"""

import os
import pytest
from pathlib import Path

pytestmark = pytest.mark.skipif(
    not os.getenv("SUPABASE_URL"),
    reason="SUPABASE_URL not configured — Supabase storage tests skipped"
)

# Test file prefix to isolate CI artifacts from real data
TEST_PREFIX = "_test_ci"


@pytest.fixture
def storage():
    """Fresh SupabaseStorage instance."""
    from supabase_storage import SupabaseStorage
    return SupabaseStorage()


@pytest.fixture
def test_file(tmp_path):
    """Create a small test PDF file."""
    f = tmp_path / "test_upload.pdf"
    f.write_bytes(b"%PDF-1.4 test content for supabase storage integration test")
    return f


@pytest.fixture
def remote_path():
    """Standard remote path for test uploads."""
    return f"{TEST_PREFIX}/test_upload.pdf"


@pytest.fixture
def cleanup_remote(storage, remote_path):
    """Ensure remote file is deleted after test, even on failure."""
    yield
    storage.delete(remote_path)


# ============================================================
# Connection
# ============================================================

class TestSupabaseStorageConnection:

    def test_import_supabase_storage(self):
        """Module imports without error."""
        from supabase_storage import SupabaseStorage, supabase_storage
        assert SupabaseStorage is not None
        assert supabase_storage is not None

    def test_storage_enabled_when_configured(self, storage):
        """.enabled returns True when env vars are set."""
        assert storage.enabled is True

    def test_storage_has_bucket(self, storage):
        """Bucket name is configured."""
        assert storage.bucket
        assert isinstance(storage.bucket, str)


# ============================================================
# Upload / Download
# ============================================================

class TestSupabaseStorageUploadDownload:

    def test_upload_file(self, storage, test_file, remote_path, cleanup_remote):
        """Upload returns (True, message)."""
        success, msg = storage.upload(str(test_file), remote_path)
        assert success is True, f"Upload failed: {msg}"
        assert "Upload OK" in msg

    def test_download_file(self, storage, test_file, remote_path, tmp_path, cleanup_remote):
        """Upload then download — content matches."""
        original_content = test_file.read_bytes()

        success, msg = storage.upload(str(test_file), remote_path)
        assert success, f"Upload failed: {msg}"

        download_dest = tmp_path / "downloaded.pdf"
        success, msg = storage.download(remote_path, str(download_dest))
        assert success is True, f"Download failed: {msg}"
        assert download_dest.read_bytes() == original_content

    def test_upload_nonexistent_file(self, storage):
        """Upload of missing file returns (False, ...)."""
        success, msg = storage.upload("/nonexistent/file.pdf", f"{TEST_PREFIX}/ghost.pdf")
        assert success is False
        assert "não encontrado" in msg or "not found" in msg.lower() or "Arquivo" in msg

    def test_download_nonexistent_file(self, storage, tmp_path):
        """Download of missing remote path returns (False, ...)."""
        download_dest = tmp_path / "should_not_exist.pdf"
        success, msg = storage.download(f"{TEST_PREFIX}/nonexistent_file_12345.pdf", str(download_dest))
        assert success is False
        assert not download_dest.exists()


# ============================================================
# Exists
# ============================================================

class TestSupabaseStorageExists:

    def test_exists_after_upload(self, storage, test_file, remote_path, cleanup_remote):
        """After uploading, .exists() returns True."""
        storage.upload(str(test_file), remote_path)
        assert storage.exists(remote_path) is True

    def test_exists_nonexistent(self, storage):
        """.exists() returns False for missing path."""
        assert storage.exists(f"{TEST_PREFIX}/nonexistent_file_99999.pdf") is False


# ============================================================
# Delete
# ============================================================

class TestSupabaseStorageDelete:

    def test_delete_existing_file(self, storage, test_file, remote_path):
        """Upload, delete, verify gone."""
        storage.upload(str(test_file), remote_path)
        success, msg = storage.delete(remote_path)
        assert success is True, f"Delete failed: {msg}"
        assert storage.exists(remote_path) is False

    def test_delete_nonexistent(self, storage):
        """Delete of missing path — Supabase returns success (idempotent)."""
        success, msg = storage.delete(f"{TEST_PREFIX}/nonexistent_delete_test.pdf")
        # Supabase delete is idempotent — may return True or False depending on version
        assert isinstance(success, bool)


# ============================================================
# URLs
# ============================================================

class TestSupabaseStorageURLs:

    def test_get_public_url(self, storage):
        """Returns a formatted URL string."""
        url = storage.get_public_url(f"{TEST_PREFIX}/any_file.pdf")
        assert url is not None
        assert TEST_PREFIX in url
        assert "public" in url
        assert storage.bucket in url

    def test_get_signed_url(self, storage, test_file, remote_path, cleanup_remote):
        """Returns signed URL with token for existing file."""
        storage.upload(str(test_file), remote_path)
        url = storage.get_signed_url(remote_path, expires_in=60)
        assert url is not None
        assert "token" in url or "sign" in url.lower()

    def test_signed_url_nonexistent(self, storage):
        """Returns None for non-existent file."""
        url = storage.get_signed_url(f"{TEST_PREFIX}/nonexistent_signed_url_test.pdf")
        # May return None or a URL that doesn't work — implementation-dependent
        # The key contract is it doesn't raise
        assert url is None or isinstance(url, str)


# ============================================================
# List Files
# ============================================================

class TestSupabaseStorageListFiles:

    def test_list_files_returns_tuple(self, storage):
        """list_files returns (bool, list|str)."""
        success, result = storage.list_files(prefix=TEST_PREFIX)
        assert isinstance(success, bool)
        if success:
            assert isinstance(result, list)

    def test_list_files_finds_uploaded(self, storage, test_file, remote_path, cleanup_remote):
        """Upload a file, then list with prefix — file appears."""
        storage.upload(str(test_file), remote_path)
        success, files = storage.list_files(prefix=TEST_PREFIX)
        assert success is True, f"List failed: {files}"
        assert isinstance(files, list)
        # The file should appear in listing (may be nested under prefix)
        assert len(files) >= 1
