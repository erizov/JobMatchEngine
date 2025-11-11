"""Build Markdown documents from parsed resume data."""

from pathlib import Path

from app.models import ParsedResume


class MarkdownBuilder:
    """Build Markdown documents."""

    def build_resume(self, resume: ParsedResume, output_path: Path) -> None:
        """
        Build Markdown resume.

        Args:
            resume: Parsed resume data
            output_path: Path to save MD file
        """
        lines = []

        # Contact information
        if resume.contact.name:
            lines.append(f"# {resume.contact.name}\n")
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
            lines.append(f"## {headers['summary']}\n")
            lines.append(resume.summary)
            lines.append("")

        # Experience
        if resume.experience:
            lines.append(f"## {headers['experience']}\n")
            for exp in resume.experience:
                # Only add valid experience entries
                if exp.title and exp.title != "Unknown" and exp.title.strip():
                    # Skip if title looks like a section header or summary text
                    if not any(keyword in exp.title.lower() for keyword in ["experience", "summary", "skills", "education", "опыт", "резюме", "навыки", "образование"]):
                        lines.append(f"### {exp.title}")
                        if exp.company and exp.company != "Unknown":
                            lines.append(f"**{exp.company}**")
                        if exp.dates:
                            lines.append(f"*{exp.dates}*")
                        lines.append("")
                        for bullet in exp.bullets:
                            if bullet and bullet.strip():
                                lines.append(f"- {bullet}")
                        lines.append("")

        # Skills
        if resume.skills:
            lines.append(f"## {headers['skills']}\n")
            lines.append(", ".join(resume.skills))
            lines.append("")

        # Education
        if resume.education:
            lines.append(f"## {headers['education']}\n")
            for edu in resume.education:
                if edu.degree:
                    lines.append(f"**{edu.degree}**")
                if edu.institution:
                    lines.append(edu.institution)
                if edu.dates:
                    lines.append(f"*{edu.dates}*")
                if edu.details:
                    lines.append(edu.details)
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
                "summary": "Professional Summary",
                "experience": "Experience",
                "skills": "Skills",
                "education": "Education",
            }

    def build_cover_letter(
        self, cover_letter_text: str, contact_info, output_path: Path
    ) -> None:
        """
        Build Markdown cover letter.

        Args:
            cover_letter_text: Cover letter text
            contact_info: Contact information
            output_path: Path to save MD file
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

        # Cover letter text
        lines.append(cover_letter_text)

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

