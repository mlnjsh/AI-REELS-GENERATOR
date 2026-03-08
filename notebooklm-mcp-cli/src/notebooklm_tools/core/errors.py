# src/notebooklm_tools/core/errors.py
"""Exception classes for NotebookLM API artifacts and client errors.

This module contains exception classes used throughout the NotebookLM API client
for artifact operations (download, parse, status) and authentication errors.

For CLI-specific exceptions (with hint messages), see exceptions.py.
"""


class NotebookLMError(Exception):
    """Base exception for NotebookLM errors.
    
    All artifact-related and client-level errors inherit from this class.
    """
    pass


class ArtifactError(NotebookLMError):
    """Base exception for artifact errors.
    
    Covers all errors related to studio artifacts (audio, video, reports, etc.)
    including generation, download, and parsing failures.
    """
    pass


class ArtifactNotReadyError(ArtifactError):
    """Raised when an artifact is not ready for download.
    
    This occurs when attempting to download an artifact that:
    - Is still being generated
    - Does not exist
    - Has failed generation
    """
    def __init__(self, artifact_type: str, artifact_id: str | None = None):
        msg = f"{artifact_type} is not ready or does not exist"
        if artifact_id:
            msg += f" (ID: {artifact_id})"
        super().__init__(msg)
        self.artifact_type = artifact_type
        self.artifact_id = artifact_id


class ArtifactParseError(ArtifactError):
    """Raised when artifact metadata cannot be parsed.
    
    This occurs when the API response structure has changed or
    contains unexpected data that cannot be processed.
    """
    def __init__(self, artifact_type: str, details: str = "", cause: Exception | None = None):
        msg = f"Failed to parse {artifact_type} metadata: {details}"
        super().__init__(msg)
        self.__cause__ = cause
        self.artifact_type = artifact_type
        self.details = details


class ArtifactDownloadError(ArtifactError):
    """Raised when artifact download fails.
    
    This occurs during HTTP download of binary artifacts when:
    - Server returns an error status
    - Network issues occur
    - Response is invalid
    """
    def __init__(self, artifact_type: str, details: str = ""):
        super().__init__(f"Failed to download {artifact_type}: {details}")
        self.artifact_type = artifact_type
        self.details = details


class ArtifactNotFoundError(ArtifactError):
    """Raised when a specific artifact ID is not found.
    
    This occurs when requesting a specific artifact by ID that
    doesn't exist in the notebook's studio artifacts.
    """
    def __init__(self, artifact_id: str, artifact_type: str = "artifact"):
        super().__init__(f"{artifact_type} not found: {artifact_id}")
        self.artifact_id = artifact_id
        self.artifact_type = artifact_type


class ClientAuthenticationError(Exception):
    """Raised when authentication fails (HTTP 401/403 or RPC Error 16).
    
    This is a client-level exception separate from NotebookLMError hierarchy.
    It indicates that the session/cookies have expired and re-authentication
    is required.
    
    Note: This class is aliased to `AuthenticationError` in client.py for
    backward compatibility, but that name also exists in exceptions.py with
    a different implementation (CLI-focused with hints).
    """
    pass
