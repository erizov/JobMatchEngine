"""Parser for .doc and .rtf files using Microsoft Word COM (Windows only)."""

import sys
from pathlib import Path
from typing import Optional

if sys.platform == "win32":
    try:
        import win32com.client
    except ImportError:
        win32com = None
else:
    win32com = None

from app.models import ParsedResume


class WordCOMParser:
    """Parser for DOC and RTF files using Word COM (Windows only)."""

    def __init__(self):
        """Initialize parser."""
        if sys.platform != "win32":
            raise RuntimeError(
                "Word COM parser is only available on Windows"
            )
        if win32com is None:
            raise ImportError(
                "pywin32 is required for Word COM parser. "
                "Install with: pip install pywin32"
            )

    def parse(self, file_path: Path) -> ParsedResume:
        """
        Parse a DOC or RTF file using Word COM.

        Args:
            file_path: Path to the file

        Returns:
            ParsedResume object
        """
        word_app = win32com.client.Dispatch("Word.Application")
        word_app.Visible = False

        try:
            doc = word_app.Documents.Open(str(file_path.absolute()))

            # Extract text from all paragraphs
            paragraphs = []
            for para in doc.Paragraphs:
                paragraphs.append(para.Range.Text)

            raw_text = "\n".join(paragraphs)

            # Close document
            doc.Close()

            # Use SectionExtractor for parsing
            from app.utils.section_extractor import SectionExtractor

            extractor = SectionExtractor()
            contact = extractor.extract_contact(raw_text)
            summary = extractor.extract_summary(raw_text)
            experience = extractor.extract_experience(raw_text)
            skills = extractor.extract_skills(raw_text)
            education = extractor.extract_education(raw_text)

            return ParsedResume(
                contact=contact,
                summary=summary,
                experience=experience,
                skills=skills,
                education=education,
                language="en",
                raw_text=raw_text,
            )

        finally:
            word_app.Quit()

