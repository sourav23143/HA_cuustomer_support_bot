"""
Tests for RAG ingestion and retrieval.
"""

import pytest
from app.rag.ingestion import clean_document_text


class TestDocumentCleaning:
    def test_removes_demo_disclaimer(self):
        text = "*This document is fictional and for demo purposes only.*\n\nActual content."
        cleaned = clean_document_text(text)
        assert "fictional" not in cleaned
        assert "Actual content" in cleaned

    def test_collapses_newlines(self):
        text = "Line 1\n\n\n\n\nLine 2"
        cleaned = clean_document_text(text)
        assert "\n\n\n" not in cleaned

    def test_preserves_content(self):
        text = "# Title\n\nParagraph one.\n\nParagraph two."
        cleaned = clean_document_text(text)
        assert "Title" in cleaned
        assert "Paragraph one" in cleaned
