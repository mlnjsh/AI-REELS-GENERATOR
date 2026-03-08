# tests/core/test_errors.py
"""Tests for artifact exception classes."""

from notebooklm_tools.core.errors import (
    NotebookLMError,
    ArtifactError,
    ArtifactNotReadyError,
    ArtifactParseError,
    ArtifactDownloadError,
    ArtifactNotFoundError,
    ClientAuthenticationError,
)


def test_artifact_not_ready_error():
    """Test ArtifactNotReadyError includes artifact type and ID."""
    err = ArtifactNotReadyError("audio", "abc-123")
    assert "audio" in str(err)
    assert "abc-123" in str(err)


def test_artifact_not_ready_error_no_id():
    """Test ArtifactNotReadyError without artifact ID."""
    err = ArtifactNotReadyError("video")
    assert "video" in str(err)
    assert "not ready" in str(err)


def test_artifact_parse_error():
    """Test ArtifactParseError includes type and details."""
    err = ArtifactParseError("video", details="Invalid structure")
    assert "video" in str(err)
    assert "Invalid structure" in str(err)


def test_artifact_download_error():
    """Test ArtifactDownloadError includes type and details."""
    err = ArtifactDownloadError("infographic", "HTTP 403")
    assert "infographic" in str(err)
    assert "HTTP 403" in str(err)


def test_artifact_not_found_error():
    """Test ArtifactNotFoundError stores artifact info."""
    err = ArtifactNotFoundError("abc-123", "report")
    assert "abc-123" in str(err)
    assert "report" in str(err)
    assert err.artifact_id == "abc-123"
    assert err.artifact_type == "report"


def test_client_authentication_error():
    """Test ClientAuthenticationError can be raised."""
    err = ClientAuthenticationError("Session expired")
    assert "Session expired" in str(err)


def test_exception_hierarchy():
    """Test exception inheritance chain."""
    assert issubclass(ArtifactError, NotebookLMError)
    assert issubclass(ArtifactNotReadyError, ArtifactError)
    assert issubclass(ArtifactParseError, ArtifactError)
    assert issubclass(ArtifactDownloadError, ArtifactError)
    assert issubclass(ArtifactNotFoundError, ArtifactError)
    # ClientAuthenticationError is separate from NotebookLMError
    assert issubclass(ClientAuthenticationError, Exception)
