"""Build DOCX documents from parsed resume data."""

from pathlib import Path

from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from app.models import ParsedResume


class DocxBuilder:
    """Build DOCX documents."""

    def __init__(self):
        """Initialize builder."""
        pass

    def build_resume(self, resume: ParsedResume, output_path: Path) -> None:
        """
        Build DOCX resume from parsed data.

        Args:
            resume: Parsed resume data
            output_path: Path to save DOCX file
        """
        doc = Document()

        # Set default font
        style = doc.styles["Normal"]
        font = style.font
        font.name = "Calibri"
        font.size = Pt(11)

        # Add contact information
        self._add_contact(doc, resume.contact)

        # Add summary
        if resume.summary:
            self._add_section_header(doc, "Professional Summary")
            self._add_paragraph(doc, resume.summary)

        # Add experience
        if resume.experience:
            self._add_section_header(doc, "Experience")
            for exp in resume.experience:
                self._add_experience_entry(doc, exp)

        # Add skills
        if resume.skills:
            self._add_section_header(doc, "Skills")
            skills_text = ", ".join(resume.skills)
            self._add_paragraph(doc, skills_text)

        # Add education
        if resume.education:
            self._add_section_header(doc, "Education")
            for edu in resume.education:
                self._add_education_entry(doc, edu)

        # Save document
        doc.save(str(output_path))

    def build_cover_letter(
        self, cover_letter_text: str, contact_info, output_path: Path
    ) -> None:
        """
        Build DOCX cover letter.

        Args:
            cover_letter_text: Cover letter text
            contact_info: Contact information
            output_path: Path to save DOCX file
        """
        doc = Document()

        # Set default font
        style = doc.styles["Normal"]
        font = style.font
        font.name = "Calibri"
        font.size = Pt(11)

        # Add contact info at top
        if contact_info.name:
            para = doc.add_paragraph(contact_info.name)
            para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        if contact_info.email:
            para = doc.add_paragraph(contact_info.email)
            para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        if contact_info.phone:
            para = doc.add_paragraph(contact_info.phone)
            para.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        # Add date
        from datetime import datetime

        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        para.add_run(datetime.now().strftime("%B %d, %Y"))

        # Add spacing
        doc.add_paragraph()

        # Add cover letter text
        paragraphs = cover_letter_text.split("\n\n")
        for para_text in paragraphs:
            if para_text.strip():
                self._add_paragraph(doc, para_text.strip())

        # Save document
        doc.save(str(output_path))

    def _add_contact(self, doc: Document, contact) -> None:
        """Add contact information."""
        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER

        if contact.name:
            run = para.add_run(contact.name)
            run.bold = True
            run.font.size = Pt(16)

        if contact.email:
            doc.add_paragraph(contact.email).alignment = WD_ALIGN_PARAGRAPH.CENTER
        if contact.phone:
            doc.add_paragraph(contact.phone).alignment = WD_ALIGN_PARAGRAPH.CENTER
        if contact.location:
            doc.add_paragraph(contact.location).alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_paragraph()  # Spacing

    def _add_section_header(self, doc: Document, title: str) -> None:
        """Add section header."""
        para = doc.add_paragraph()
        run = para.add_run(title)
        run.bold = True
        run.font.size = Pt(12)
        # Note: font.color is read-only in python-docx, use run.font.color.rgb instead
        try:
            run.font.color.rgb = RGBColor(0, 51, 102)
        except AttributeError:
            # Fallback if color setting fails
            pass

    def _add_paragraph(self, doc: Document, text: str) -> None:
        """Add paragraph."""
        doc.add_paragraph(text)

    def _add_experience_entry(self, doc: Document, exp) -> None:
        """Add experience entry."""
        # Title and company
        para = doc.add_paragraph()
        run = para.add_run(exp.title)
        run.bold = True
        if exp.company:
            para.add_run(f" at {exp.company}")

        # Dates
        if exp.dates:
            para = doc.add_paragraph(exp.dates)
            para.italic = True

        # Bullets
        for bullet in exp.bullets:
            para = doc.add_paragraph(bullet, style="List Bullet")

        doc.add_paragraph()  # Spacing

    def _add_education_entry(self, doc: Document, edu) -> None:
        """Add education entry."""
        para = doc.add_paragraph()
        if edu.degree:
            run = para.add_run(edu.degree)
            run.bold = True
            if edu.institution:
                para.add_run(f", {edu.institution}")
        elif edu.institution:
            para.add_run(edu.institution).bold = True

        if edu.dates:
            doc.add_paragraph(edu.dates).italic = True

        if edu.details:
            doc.add_paragraph(edu.details)

        doc.add_paragraph()  # Spacing

