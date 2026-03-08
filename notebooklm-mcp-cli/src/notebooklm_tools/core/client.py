#!/usr/bin/env python3
"""NotebookLM MCP API client (notebooklm.google.com).

This module provides the full NotebookLMClient that inherits from BaseClient
and adds all domain-specific operations (notebooks, sources, studio, etc.).

Internal API. See CLAUDE.md for full documentation.
"""

import json
import logging
import re

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import httpx

from . import constants
from .base import BaseClient, DEFAULT_TIMEOUT, SOURCE_ADD_TIMEOUT, logger
from .conversation import ConversationMixin
from .download import DownloadMixin
from .notebooks import NotebookMixin
from .notes import NotesMixin
from .research import ResearchMixin
from .sharing import SharingMixin
from .sources import SourceMixin
from .studio import StudioMixin
from .exports import ExportMixin


# Import utility functions from utils module
from .utils import (
    RPC_NAMES,
    _format_debug_json,
    _decode_request_body,
    _parse_url_params,
    parse_timestamp,
    extract_cookies_from_chrome_export,
)

# Import dataclasses from data_types module (re-exported for backward compatibility)
from .data_types import (
    ConversationTurn,
    Collaborator,
    ShareStatus,
    Notebook,
)


# Import exception classes from errors module (re-exported for backward compatibility)
from .errors import (
    NotebookLMError,
    ArtifactError,
    ArtifactNotReadyError,
    ArtifactParseError,
    ArtifactDownloadError,
    ArtifactNotFoundError,
    ClientAuthenticationError,
)

# Backward compatibility alias - code importing AuthenticationError from client.py
# will get the ClientAuthenticationError from errors.py
AuthenticationError = ClientAuthenticationError


# Ownership constants (from metadata position 0) - re-exported for backward compatibility
OWNERSHIP_MINE = constants.OWNERSHIP_MINE
OWNERSHIP_SHARED = constants.OWNERSHIP_SHARED


class NotebookLMClient(ExportMixin, DownloadMixin, StudioMixin, ResearchMixin, ConversationMixin, SourceMixin, SharingMixin, NotebookMixin, NotesMixin):
    """Client for NotebookLM MCP internal API.

    This class extends BaseClient with all domain-specific operations:
    - Notebook management (list, create, rename, delete)
    - Source management (add, sync, delete)
    - Query/chat operations
    - Studio content (audio, video, reports, flashcards, etc.)
    - Research operations
    - Sharing and collaboration
    - Notes management (create, list, update, delete)

    All HTTP/RPC infrastructure is provided by the BaseClient base class.
    """
    
    # Note: All RPC IDs, API constants, and infrastructure methods are inherited from BaseClient

    # =========================================================================
    # Conversation Operations (inherited from ConversationMixin)
    # =========================================================================
    # The following methods are provided by ConversationMixin:
    # - query
    # - clear_conversation
    # - get_conversation_history
    # - _build_conversation_history
    # - _cache_conversation_turn
    # - _parse_query_response
    # - _extract_answer_from_chunk
    # - _extract_source_ids_from_notebook

    # =========================================================================
    # Notebook Operations (inherited from NotebookMixin)
    # =========================================================================
    # The following methods are provided by NotebookMixin:
    # - list_notebooks
    # - get_notebook
    # - get_notebook_summary
    # - create_notebook
    # - rename_notebook
    # - configure_chat
    # - delete_notebook

    # =========================================================================
    # Sharing Operations (inherited from SharingMixin)
    # =========================================================================
    # The following methods are provided by SharingMixin:
    # - get_share_status
    # - set_public_access
    # - add_collaborator

    # =========================================================================
    # Source Operations (inherited from SourceMixin)
    # =========================================================================
    # The following methods are provided by SourceMixin:
    # - check_source_freshness
    # - sync_drive_source
    # - delete_source
    # - get_notebook_sources_with_types
    # - add_url_source
    # - add_text_source
    # - add_drive_source
    # - upload_file
    # - get_source_guide
    # - get_source_fulltext

    # =========================================================================
    # Research Operations (inherited from ResearchMixin)
    # =========================================================================
    # The following methods are provided by ResearchMixin:
    # - start_research
    # - poll_research
    # - import_research_sources
    # - _parse_research_sources

    # =========================================================================
    # Studio Operations (provided by StudioMixin)
    # =========================================================================
    # The following methods are provided by StudioMixin:
    # - create_audio_overview, create_video_overview
    # - poll_studio_status, get_studio_status
    # - delete_studio_artifact, delete_mind_map
    # - create_infographic, create_slide_deck
    # - create_report, create_flashcards, create_quiz
    # - create_data_table, generate_mind_map, save_mind_map, list_mind_maps

    # =========================================================================
    # Notes Operations (inherited from NotesMixin)
    # =========================================================================
    # The following methods are provided by NotesMixin:
    # - create_note
    # - list_notes
    # - update_note
    # - delete_note

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None
