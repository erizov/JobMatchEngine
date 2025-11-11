"""Parser for .docx files using python-docx."""

from pathlib import Path
from typing import Optional

from docx import Document

from app.models import ContactInfo, Education, Experience, ParsedResume
from app.utils.section_extractor import SectionExtractor


class DocxParser:
    """Parser for DOCX files."""

    def __init__(self):
        """Initialize parser."""
        self.extractor = SectionExtractor()

    def parse(self, file_path: Path) -> ParsedResume:
        """
        Parse a DOCX file and extract structured resume data.

        Args:
            file_path: Path to the DOCX file

        Returns:
            ParsedResume object
        """
        doc = Document(file_path)

        # Extract raw text
        raw_text = "\n".join([para.text for para in doc.paragraphs])

        # Extract structured sections using SectionExtractor
        contact = self.extractor.extract_contact(raw_text)
        summary = self.extractor.extract_summary(raw_text)
        experience = self.extractor.extract_experience(raw_text)
        skills = self.extractor.extract_skills(raw_text)
        education = self.extractor.extract_education(raw_text)

        # TODO: Language detection will be added in analyzer module
        language = "en"  # Placeholder

        return ParsedResume(
            contact=contact,
            summary=summary,
            experience=experience,
            skills=skills,
            education=education,
            language=language,
            raw_text=raw_text,
        )

