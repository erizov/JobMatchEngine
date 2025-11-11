"""Parser for .txt and .md files."""

from pathlib import Path

from app.models import ParsedResume
from app.utils.section_extractor import SectionExtractor


class TextParser:
    """Parser for plain text and markdown files."""

    def __init__(self):
        """Initialize parser."""
        self.extractor = SectionExtractor()

    def parse(self, file_path: Path) -> ParsedResume:
        """
        Parse a text or markdown file.

        Args:
            file_path: Path to the file

        Returns:
            ParsedResume object
        """
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        # Extract structured sections
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

