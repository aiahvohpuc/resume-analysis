"""Tests for resume parser modules."""

from unittest.mock import Mock, patch

import pytest
from src.parser.pdf_parser import PDFParser
from src.parser.text_parser import TextParser


class TestTextParser:
    """Tests for TextParser class."""

    def test_create_text_parser(self):
        """Should create a text parser instance."""
        parser = TextParser()
        assert parser is not None

    def test_parse_empty_text(self):
        """Should handle empty text input."""
        parser = TextParser()
        result = parser.parse("")
        assert result == ""

    def test_parse_whitespace_text(self):
        """Should trim whitespace from text."""
        parser = TextParser()
        result = parser.parse("  Hello World  \n\n")
        assert result == "Hello World"

    def test_extract_sections_from_text(self):
        """Should extract common resume sections."""
        parser = TextParser()
        sample_text = """
        John Doe
        Email: john@example.com

        Experience
        Software Engineer at TechCorp
        2020-2023

        Education
        BS Computer Science, Seoul National University
        2015-2019

        Skills
        Python, JavaScript, Docker
        """
        sections = parser.extract_sections(sample_text)

        assert "contact" in sections or "header" in sections
        assert "experience" in sections
        assert "education" in sections
        assert "skills" in sections

    def test_extract_contact_info(self):
        """Should extract contact information from text."""
        parser = TextParser()
        text = """
        Jane Smith
        jane.smith@email.com
        010-1234-5678
        Seoul, Korea
        """
        contact = parser.extract_contact_info(text)

        assert contact["name"] is not None
        assert "email" in contact

    def test_extract_skills_list(self):
        """Should extract skills as a list."""
        parser = TextParser()
        text = """
        Skills:
        Python, JavaScript, TypeScript, React, Docker, Kubernetes
        """
        skills = parser.extract_skills(text)

        assert isinstance(skills, list)
        assert len(skills) > 0


class TestPDFParser:
    """Tests for PDFParser class."""

    def test_create_pdf_parser(self):
        """Should create a PDF parser instance."""
        parser = PDFParser()
        assert parser is not None

    def test_parse_nonexistent_file(self):
        """Should raise error for non-existent file."""
        parser = PDFParser()
        with pytest.raises(FileNotFoundError):
            parser.parse("/nonexistent/file.pdf")

    def test_extract_text_from_pdf(self):
        """Should extract text from a PDF file."""
        parser = PDFParser()

        # Create a mock PDF with text
        with patch("src.parser.pdf_parser.os.path.exists", return_value=True):
            with patch("src.parser.pdf_parser.pdfplumber.open") as mock_open:
                mock_page = Mock()
                mock_page.extract_text.return_value = "Sample resume text"
                mock_pdf = Mock()
                mock_pdf.pages = [mock_page]
                mock_pdf.__enter__ = Mock(return_value=mock_pdf)
                mock_pdf.__exit__ = Mock(return_value=False)
                mock_open.return_value = mock_pdf

                result = parser.extract_text("/fake/path.pdf")

                assert result == "Sample resume text"

    def test_parse_returns_text_parser_result(self):
        """Should use TextParser to process extracted PDF text."""
        parser = PDFParser()

        with patch.object(parser, "extract_text") as mock_extract:
            mock_extract.return_value = "John Doe\njohn@email.com\n\nExperience\nDeveloper"

            with patch("src.parser.pdf_parser.os.path.exists", return_value=True):
                result = parser.parse("/fake/resume.pdf")

            assert isinstance(result, dict)
            assert "raw_text" in result
