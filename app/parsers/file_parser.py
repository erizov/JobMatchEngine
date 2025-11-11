"""Main file parser that routes to format-specific parsers."""

from pathlib import Path
from typing import Optional

from app.models import ParsedResume


class FileParser:
    """Main parser that routes to format-specific parsers."""

    def __init__(self):
        """Initialize parser."""
        pass

    def parse(self, file_path: Path) -> ParsedResume:
        """
        Parse a resume file and return structured data.

        Args:
            file_path: Path to the resume file

        Returns:
            ParsedResume object with structured data

        Raises:
            ValueError: If file format is not supported
        """
        suffix = file_path.suffix.lower()

        if suffix == ".docx":
            from app.parsers.docx_parser import DocxParser

            parser = DocxParser()
            return parser.parse(file_path)

        elif suffix in [".doc", ".rtf"]:
            from app.parsers.word_com_parser import WordCOMParser

            parser = WordCOMParser()
            return parser.parse(file_path)

        elif suffix in [".txt", ".md"]:
            from app.parsers.text_parser import TextParser

            parser = TextParser()
            return parser.parse(file_path)

        else:
            raise ValueError(
                f"Unsupported file format: {suffix}. "
                "Supported formats: .docx, .doc, .rtf, .txt, .md"
            )

