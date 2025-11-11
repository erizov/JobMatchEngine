"""Build plain text documents from parsed resume data."""

from pathlib import Path

from app.models import ParsedResume


class TextBuilder:
    """Build plain text documents."""

    def build_resume(self, resume: ParsedResume, output_path: Path) -> None:
        """
        Build plain text resume.

        Args:
            resume: Parsed resume data
            output_path: Path to save TXT file
        """
        lines = []

        # Contact information
        if resume.contact.name:
            lines.append(resume.contact.name.upper())
            lines.append("")
        if resume.contact.email:
            lines.append(f"Email: {resume.contact.email}")
        if resume.contact.phone:
            lines.append(f"Phone: {resume.contact.phone}")
        if resume.contact.location:
            lines.append(f"Location: {resume.contact.location}")
        lines.append("")

        # Determine language for headers
        language = resume.language or "en"
        headers = self._get_section_headers(language)

        # Summary
        if resume.summary:
            lines.append(headers["summary"].upper())
            lines.append("-" * 50)
            lines.append(resume.summary)
            lines.append("")

        # Experience
        if resume.experience:
            lines.append(headers["experience"].upper())
            lines.append("-" * 50)
            for exp in resume.experience:
                # Only add valid experience entries
                if exp.title and exp.title != "Unknown" and exp.title.strip():
                    # Skip if title looks like a section header or summary text
                    if not any(keyword in exp.title.lower() for keyword in ["experience", "summary", "skills", "education", "опыт", "резюме", "навыки", "образование"]):
                        lines.append(exp.title)
                        if exp.company and exp.company != "Unknown":
                            lines.append(exp.company)
                        if exp.dates:
                            lines.append(exp.dates)
                        lines.append("")
                        for bullet in exp.bullets:
                            if bullet and bullet.strip():
                                lines.append(f"  • {bullet}")
                        lines.append("")

        # Skills
        if resume.skills:
            lines.append(headers["skills"].upper())
            lines.append("-" * 50)
            lines.append(", ".join(resume.skills))
            lines.append("")

        # Education
        if resume.education:
            lines.append(headers["education"].upper())
            lines.append("-" * 50)
            for edu in resume.education:
                if edu.degree:
                    lines.append(edu.degree)
                if edu.institution:
                    lines.append(edu.institution)
                if edu.dates:
                    lines.append(edu.dates)
                lines.append("")

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
    
    def _get_section_headers(self, language: str) -> dict:
        """Get section headers based on language."""
        if language == "ru":
            return {
                "summary": "Профессиональное резюме",
                "experience": "Опыт работы",
                "skills": "Навыки",
                "education": "Образование",
            }
        else:
            return {
                "summary": "PROFESSIONAL SUMMARY",
                "experience": "EXPERIENCE",
                "skills": "SKILLS",
                "education": "EDUCATION",
            }

    def build_cover_letter(
        self, cover_letter_text: str, contact_info, output_path: Path
    ) -> None:
        """
        Build plain text cover letter.

        Args:
            cover_letter_text: Cover letter text
            contact_info: Contact information
            output_path: Path to save TXT file
        """
        lines = []

        # Contact info
        if contact_info.name:
            lines.append(contact_info.name)
        if contact_info.email:
            lines.append(contact_info.email)
        if contact_info.phone:
            lines.append(contact_info.phone)
        lines.append("")

        # Date
        from datetime import datetime

        lines.append(datetime.now().strftime("%B %d, %Y"))
        lines.append("")
        lines.append("")

        # Cover letter text
        lines.append(cover_letter_text)

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

