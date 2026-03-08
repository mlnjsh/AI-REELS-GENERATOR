#!/usr/bin/env python3
"""Tests for ResearchMixin."""

import pytest
from unittest.mock import patch

from notebooklm_tools.core.base import BaseClient
from notebooklm_tools.core.research import ResearchMixin


class TestResearchMixinImport:
    """Test that ResearchMixin can be imported correctly."""

    def test_research_mixin_import(self):
        """Test that ResearchMixin can be imported."""
        assert ResearchMixin is not None

    def test_research_mixin_inherits_base(self):
        """Test that ResearchMixin inherits from BaseClient."""
        assert issubclass(ResearchMixin, BaseClient)

    def test_research_mixin_has_methods(self):
        """Test that ResearchMixin has expected methods."""
        expected_methods = [
            "start_research",
            "poll_research",
            "import_research_sources",
            "_parse_research_sources",
        ]
        for method in expected_methods:
            assert hasattr(ResearchMixin, method), f"Missing method: {method}"


class TestResearchMixinMethods:
    """Test ResearchMixin method behavior."""

    def test_start_research_validates_source(self):
        """Test that start_research validates source parameter."""
        mixin = ResearchMixin(cookies={"test": "cookie"}, csrf_token="test")
        
        with pytest.raises(ValueError, match="Invalid source"):
            mixin.start_research("notebook-id", "query", source="invalid")

    def test_start_research_validates_mode(self):
        """Test that start_research validates mode parameter."""
        mixin = ResearchMixin(cookies={"test": "cookie"}, csrf_token="test")
        
        with pytest.raises(ValueError, match="Invalid mode"):
            mixin.start_research("notebook-id", "query", mode="invalid")

    def test_start_research_validates_deep_with_drive(self):
        """Test that start_research rejects deep mode with drive source."""
        mixin = ResearchMixin(cookies={"test": "cookie"}, csrf_token="test")
        
        with pytest.raises(ValueError, match="Deep Research only supports Web"):
            mixin.start_research("notebook-id", "query", source="drive", mode="deep")

    def test_parse_research_sources_handles_empty(self):
        """Test that _parse_research_sources handles empty input."""
        mixin = ResearchMixin(cookies={"test": "cookie"}, csrf_token="test")
        
        result = mixin._parse_research_sources([])
        
        assert result == []

    def test_parse_research_sources_handles_none_input(self):
        """Test that _parse_research_sources handles non-list input."""
        mixin = ResearchMixin(cookies={"test": "cookie"}, csrf_token="test")
        
        result = mixin._parse_research_sources(None)
        
        assert result == []

    def test_import_research_sources_returns_empty_for_no_sources(self):
        """Test that import_research_sources returns empty for no sources."""
        mixin = ResearchMixin(cookies={"test": "cookie"}, csrf_token="test")
        
        result = mixin.import_research_sources("notebook-id", "task-id", [])
        
        assert result == []
