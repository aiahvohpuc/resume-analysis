"""PDF parser for resume document processing."""

import os

import pdfplumber

from src.parser.text_parser import TextParser


class PDFParser:
    """Parser for extracting text from PDF resume documents."""

    def __init__(self):
        """Initialize the PDF parser with a text parser."""
        self.text_parser = TextParser()

    def extract_text(self, file_path: str) -> str:
        """Extract raw text from a PDF file.

        Args:
            file_path: Path to the PDF file.

        Returns:
            Extracted text content from all pages.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        text_content = []

        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)

        return "\n".join(text_content)

    def parse(self, file_path: str) -> dict:
        """Parse a PDF resume file and extract structured data.

        Args:
            file_path: Path to the PDF resume file.

        Returns:
            Dictionary containing parsed resume data.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        raw_text = self.extract_text(file_path)
        cleaned_text = self.text_parser.parse(raw_text)
        sections = self.text_parser.extract_sections(cleaned_text)

        result = {
            "raw_text": raw_text,
            "cleaned_text": cleaned_text,
            "sections": sections,
        }

        # Extract contact info if header section exists
        if "header" in sections:
            result["contact"] = self.text_parser.extract_contact_info(
                sections["header"]
            )
        elif "contact" in sections:
            result["contact"] = self.text_parser.extract_contact_info(
                sections["contact"]
            )

        # Extract skills if skills section exists
        if "skills" in sections:
            result["skills"] = self.text_parser.extract_skills(sections["skills"])

        return result
