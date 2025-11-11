"""Utilities for extracting sections from resume text."""

import re
from typing import List, Optional, Tuple

from app.models import ContactInfo, Education, Experience


class SectionExtractor:
    """Extract structured sections from resume text."""

    # Common section headers in multiple languages
    SECTION_PATTERNS = {
        "summary": [
            r"(?i)^(summary|profile|objective|about|резюме|профиль|о себе)",
            r"(?i)^(professional summary|executive summary)",
        ],
        "experience": [
            r"(?i)^(experience|work experience|employment|work history|"
            r"опыт работы|трудовой опыт|места работы)",
            r"(?i)^(professional experience|career history)",
        ],
        "skills": [
            r"(?i)^(skills|technical skills|core competencies|"
            r"навыки|компетенции|технические навыки)",
            r"(?i)^(key skills|professional skills)",
        ],
        "education": [
            r"(?i)^(education|academic background|qualifications|"
            r"образование|квалификация)",
            r"(?i)^(educational background|academic qualifications)",
        ],
        "contact": [
            r"(?i)^(contact|contact information|personal information|"
            r"контакты|контактная информация)",
        ],
    }

    EMAIL_PATTERN = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    )
    PHONE_PATTERN = re.compile(
        r"(\+?\d{1,3}[-.\s]?)?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,9}"
    )
    LINKEDIN_PATTERN = re.compile(
        r"(?:linkedin\.com/in/|linkedin\.com/pub/)([\w-]+)", re.IGNORECASE
    )
    GITHUB_PATTERN = re.compile(
        r"github\.com/([\w-]+)", re.IGNORECASE
    )

    def extract_contact(self, text: str) -> ContactInfo:
        """
        Extract contact information from text.

        Args:
            text: Resume text

        Returns:
            ContactInfo object
        """
        # Extract email
        email_match = self.EMAIL_PATTERN.search(text)
        email = email_match.group(0) if email_match else None

        # Extract phone
        phone_match = self.PHONE_PATTERN.search(text)
        phone = phone_match.group(0) if phone_match else None

        # Extract LinkedIn
        linkedin_match = self.LINKEDIN_PATTERN.search(text)
        linkedin = (
            f"https://linkedin.com/in/{linkedin_match.group(1)}"
            if linkedin_match
            else None
        )

        # Extract GitHub
        github_match = self.GITHUB_PATTERN.search(text)
        github = (
            f"https://github.com/{github_match.group(1)}"
            if github_match
            else None
        )

        # Extract name (first line or before email)
        name = None
        lines = text.split("\n")[:10]
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip if line contains email or phone
            if email and email in line:
                continue
            if phone and phone in line:
                continue
            
            # Skip common headers
            if re.search(
                r"(?i)^(email|phone|location|address|contact|summary|experience|skills|education)",
                line,
            ):
                continue
            
            # Name is usually first substantial line (2-4 words, no digits, no special chars at start)
            words = line.split()
            if (
                2 <= len(words) <= 4
                and not any(char.isdigit() for char in line)
                and not line.startswith(("-", "•", "*", "#"))
                and not ":" in line
            ):
                name = line
                break

        return ContactInfo(
            name=name,
            email=email,
            phone=phone,
            linkedin=linkedin,
            github=github,
        )

    def extract_summary(self, text: str) -> Optional[str]:
        """
        Extract summary/profile section.

        Args:
            text: Resume text

        Returns:
            Summary text or None
        """
        summary_section = self._extract_section(text, "summary")
        if summary_section:
            # Clean up the summary
            lines = summary_section.split("\n")
            # Remove section header
            if lines:
                lines = lines[1:]
            summary = "\n".join(lines).strip()
            return summary if summary else None
        return None

    def extract_experience(self, text: str) -> List[Experience]:
        """
        Extract work experience entries.

        Args:
            text: Resume text

        Returns:
            List of Experience objects
        """
        experience_section = self._extract_section(text, "experience")
        if not experience_section:
            return []

        experiences = []
        # Split by common patterns (dates, company names, etc.)
        # Pattern: Title at Company | Dates
        # Or: Company - Title | Dates
        entries = self._split_experience_entries(experience_section)

        for entry_text in entries:
            exp = self._parse_experience_entry(entry_text)
            if exp:
                experiences.append(exp)

        return experiences

    def extract_skills(self, text: str) -> List[str]:
        """
        Extract skills section.

        Args:
            text: Resume text

        Returns:
            List of skills
        """
        skills_section = self._extract_section(text, "skills")
        if not skills_section:
            return []

        skills = []
        lines = skills_section.split("\n")[1:]  # Skip header

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Skills can be comma-separated, bullet-separated, or line-separated
            # Remove bullet points
            line = re.sub(r"^[-•*]\s*", "", line)
            line = re.sub(r"^\d+[.)]\s*", "", line)

            # Split by common separators
            if "," in line:
                items = [s.strip() for s in line.split(",")]
                skills.extend(items)
            elif "|" in line:
                items = [s.strip() for s in line.split("|")]
                skills.extend(items)
            else:
                if line:
                    skills.append(line)

        # Clean and deduplicate
        skills = [s.strip() for s in skills if s.strip()]
        return list(dict.fromkeys(skills))  # Preserve order, remove duplicates

    def extract_education(self, text: str) -> List[Education]:
        """
        Extract education entries.

        Args:
            text: Resume text

        Returns:
            List of Education objects
        """
        education_section = self._extract_section(text, "education")
        if not education_section:
            return []

        educations = []
        entries = self._split_education_entries(education_section)

        for entry_text in entries:
            edu = self._parse_education_entry(entry_text)
            if edu:
                educations.append(edu)

        return educations

    def _extract_section(self, text: str, section_name: str) -> Optional[str]:
        """Extract a specific section from text."""
        patterns = self.SECTION_PATTERNS.get(section_name, [])
        lines = text.split("\n")

        start_idx = None
        for i, line in enumerate(lines):
            for pattern in patterns:
                if re.match(pattern, line.strip()):
                    start_idx = i
                    break
            if start_idx is not None:
                break

        if start_idx is None:
            return None

        # Find end of section (next section header or end of text)
        end_idx = len(lines)
        for i in range(start_idx + 1, len(lines)):
            line = lines[i].strip()
            if not line:
                # Empty lines are OK within a section, don't break
                continue
            # Check if this is another section header
            is_header = False
            for other_section, other_patterns in self.SECTION_PATTERNS.items():
                if other_section == section_name:
                    continue
                for pattern in other_patterns:
                    if re.match(pattern, line):
                        end_idx = i
                        is_header = True
                        break
                if is_header:
                    break
            if is_header:
                break

        # Extract the section
        section_lines = lines[start_idx:end_idx]
        return "\n".join(section_lines)

    def _split_experience_entries(self, section_text: str) -> List[str]:
        """Split experience section into individual entries."""
        lines = section_text.split("\n")
        entries = []
        current_entry = []
        
        # Skip section header line if present
        if lines and re.match(r"(?i)^(experience|work experience|employment|work history|опыт работы)", lines[0].strip()):
            lines = lines[1:]

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Empty line marks end of entry
            if not line_stripped:
                if current_entry:
                    entries.append("\n".join(current_entry))
                    current_entry = []
                continue

            # Check if this is a bullet point
            is_bullet = line_stripped.startswith(('-', '•', '*')) or re.match(r'^\d+[.)]', line_stripped)
            
            # Check if this line contains dates
            has_dates = bool(re.search(r'\b(19|20)\d{2}\b', line_stripped))
            
            # If we have bullets in current entry, keep adding until empty line
            if current_entry and any(l.strip().startswith(('-', '•', '*')) for l in current_entry):
                current_entry.append(line)
            # If line is a bullet, add to current entry
            elif is_bullet:
                current_entry.append(line)
            # If current entry is empty or just has 1-2 lines (title/company/dates), add this line
            elif len(current_entry) < 3:
                current_entry.append(line)
            # Otherwise, this might be a new entry - check if it looks like a title
            elif not has_dates and not is_bullet and len(line_stripped) > 3:
                # Save current entry and start new one
                if current_entry:
                    entries.append("\n".join(current_entry))
                current_entry = [line]
            else:
                current_entry.append(line)

        if current_entry:
            entries.append("\n".join(current_entry))

        return entries

    def _parse_experience_entry(self, entry_text: str) -> Optional[Experience]:
        """Parse a single experience entry."""
        lines = [l.strip() for l in entry_text.split("\n") if l.strip()]
        if not lines:
            return None

        # Standard resume format: Title / Company / Dates / Bullets
        # Bullets start with - or • or *
        title = ""
        company = ""
        dates = ""
        bullets = []
        
        date_pattern = r"\b(19|20)\d{2}\b"
        
        # Separate lines into header (title/company/dates) and bullets
        header_lines = []
        bullet_lines = []
        
        for line in lines:
            # Check if this is a bullet point
            if line.startswith(('-', '•', '*')) or re.match(r'^\d+[.)]', line):
                bullet_lines.append(line)
            else:
                # If we haven't started bullets yet, this is a header line
                if not bullet_lines:
                    header_lines.append(line)
                else:
                    # After bullets started, non-bullet lines are still bullets (continuation)
                    bullet_lines.append(line)
        
        # Parse header lines (should be 2-3 lines: title, company, dates)
        for i, line in enumerate(header_lines):
            has_date = bool(re.search(date_pattern, line))
            
            if i == 0 and not has_date:
                # First line without date = title
                title = line
            elif i == 1 and not has_date:
                # Second line without date = company
                company = line
            elif has_date:
                # Line with date = dates
                dates_match = re.search(
                    r"(" + date_pattern + r"(\s*[-–—]\s*(" + date_pattern + r"|Present|Current))?)",
                    line,
                    re.IGNORECASE,
                )
                if dates_match:
                    dates = dates_match.group(0).strip()
                # If there's text before dates on same line, it might be company
                text_before_date = re.sub(
                    r"(" + date_pattern + r"(\s*[-–—]\s*(" + date_pattern + r"|Present|Current))?)",
                    "",
                    line,
                    flags=re.IGNORECASE
                ).strip()
                if text_before_date and not company:
                    company = text_before_date
            elif not title and not company:
                # Fallback: first non-date line is title
                title = line
            elif title and not company:
                # Second non-date line is company
                company = line
        
        # Parse bullets
        for line in bullet_lines:
            # Remove bullet markers
            cleaned = re.sub(r"^[-•*]\s*", "", line)
            cleaned = re.sub(r"^\d+[.)]\s*", "", cleaned)
            if cleaned.strip():
                bullets.append(cleaned.strip())

        return Experience(
            title=title or "Unknown",
            company=company or "Unknown",
            dates=dates,
            bullets=bullets,
            raw_text=entry_text,
        )

    def _split_education_entries(self, section_text: str) -> List[str]:
        """Split education section into individual entries."""
        lines = section_text.split("\n")
        entries = []
        current_entry = []

        for line in lines:
            line = line.strip()
            if not line:
                if current_entry:
                    entries.append("\n".join(current_entry))
                    current_entry = []
                continue

            # Check if this looks like a new entry (has dates or degree)
            degree_pattern = r"(?i)(bachelor|master|phd|doctorate|degree|"
            degree_pattern += r"бакалавр|магистр|диплом)"
            if re.search(degree_pattern, line) and current_entry:
                entries.append("\n".join(current_entry))
                current_entry = [line]
            else:
                current_entry.append(line)

        if current_entry:
            entries.append("\n".join(current_entry))

        return entries

    def _parse_education_entry(self, entry_text: str) -> Optional[Education]:
        """Parse a single education entry."""
        lines = [l.strip() for l in entry_text.split("\n") if l.strip()]
        if not lines:
            return None

        first_line = lines[0]

        # Extract dates
        date_pattern = r"(\d{4}|\d{1,2}/\d{4})"
        dates_match = re.search(
            r"(" + date_pattern + r"(\s*[-–—]\s*" + date_pattern + r")?)",
            first_line,
        )
        dates = dates_match.group(0).strip() if dates_match else None

        # Extract degree
        degree_pattern = r"(?i)(bachelor|master|phd|doctorate|degree|"
        degree_pattern += r"бакалавр|магистр|диплом)[\w\s]*"
        degree_match = re.search(degree_pattern, first_line)
        degree = degree_match.group(0).strip() if degree_match else None

        # Institution is usually the main part
        institution = first_line
        if degree:
            institution = institution.replace(degree, "").strip()
        if dates:
            institution = re.sub(date_pattern + r"(\s*[-–—]\s*" + date_pattern + r")?", "", institution).strip()

        # Clean up separators
        institution = re.sub(r"^[-•*|]\s*", "", institution)
        institution = re.sub(r"\s*[-•*|]\s*$", "", institution)

        details = "\n".join(lines[1:]) if len(lines) > 1 else None

        return Education(
            degree=degree,
            institution=institution or "Unknown",
            dates=dates,
            details=details,
        )

