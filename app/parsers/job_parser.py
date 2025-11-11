"""Parser for job postings from URLs or text."""

import re
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup
from trafilatura import extract

from app.analyzers.keyword_extractor import KeywordExtractor
from app.analyzers.language_detector import LanguageDetector
from app.models import JobPosting


class JobParser:
    """Parser for job postings."""

    def __init__(self):
        """Initialize parser."""
        self.extractor = KeywordExtractor()
        self.language_detector = LanguageDetector()

    async def parse_from_url(self, url: str) -> JobPosting:
        """
        Parse job posting from URL.

        Args:
            url: URL to the job posting

        Returns:
            JobPosting object
        """
        async with httpx.AsyncClient() as client:
            # Set proper headers
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            }
            response = await client.get(url, timeout=30.0, headers=headers)
            response.raise_for_status()
            
            # Get text with proper encoding handling
            try:
                html = response.text
            except UnicodeDecodeError:
                # Fallback: decode manually
                html = response.content.decode("utf-8", errors="ignore")

        # Parse HTML with BeautifulSoup first to extract structured data
        soup = BeautifulSoup(html, "lxml")
        
        # Extract title from hh.ru specific structure
        title = ""
        title_elem = soup.find("h1", {"data-qa": "vacancy-title"})
        if not title_elem:
            title_elem = soup.find("h1", class_=lambda x: x and "vacancy-title" in str(x).lower())
        if title_elem:
            title = title_elem.get_text(strip=True)
        
        # Extract company from hh.ru specific structure
        company = None
        company_elem = soup.find("a", {"data-qa": "vacancy-company-name"})
        if not company_elem:
            company_elem = soup.find("span", {"data-qa": "vacancy-company-name"})
        if company_elem:
            company = company_elem.get_text(strip=True)
        
        # Extract description
        description_elem = soup.find("div", {"data-qa": "vacancy-description"})
        if description_elem:
            text = description_elem.get_text(separator="\n", strip=True)
        else:
            # Use trafilatura for content extraction
            try:
                text = extract(html) or html
            except Exception:
                text = html
            
            # Fallback to BeautifulSoup
            if not text or len(text) < 100:
                # Remove script and style elements
                for script in soup(["script", "style", "noscript"]):
                    script.decompose()
                body = soup.find("body")
                if body:
                    text = body.get_text(separator="\n", strip=True)
                else:
                    text = soup.get_text(separator="\n", strip=True)
        
        # Parse the text
        job = self.parse_from_text(text)
        
        # Override with extracted structured data if available
        if title:
            job.title = title
        if company:
            job.company = company
        
        return job

    def parse_from_text(self, text: str) -> JobPosting:
        """
        Parse job posting from plain text.

        Args:
            text: Job posting text

        Returns:
            JobPosting object
        """
        # Detect language
        language = self.language_detector.detect_language(text)

        # Extract title (usually first line or after "Position:", "Title:", etc.)
        title = self._extract_title(text)

        # Extract company
        company = self._extract_company(text)

        # Extract location
        location = self._extract_location(text)

        # Extract requirements and responsibilities
        requirements = self._extract_requirements(text)
        responsibilities = self._extract_responsibilities(text)

        # Extract keywords
        keywords = self.extractor.extract_keywords(text, top_k=30, language=language)

        # Separate must-have and nice-to-have
        must_have, nice_to_have = self._categorize_keywords(
            keywords, requirements, text
        )

        return JobPosting(
            title=title,
            company=company,
            location=location,
            description=text,
            requirements=requirements,
            responsibilities=responsibilities,
            keywords=keywords,
            must_have_keywords=must_have,
            nice_to_have_keywords=nice_to_have,
            language=language,
            raw_text=text,
        )

    def _extract_title(self, text: str) -> str:
        """Extract job title."""
        lines = text.split("\n")[:20]
        
        # Skip common headers
        skip_patterns = [
            r"(?i)^(обязанности|требования|условия|responsibilities|requirements|qualifications)",
            r"(?i)^(компания|company|employer)",
            r"(?i)^(зарплата|salary|compensation)",
            r"(?i)^(опыт|experience)",
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip if it's a header
            if any(re.search(pattern, line) for pattern in skip_patterns):
                continue
            
            # Look for title patterns
            if re.search(r"(?i)^(position|title|job title|role|должность|вакансия):", line):
                title = re.sub(r"(?i)^(position|title|job title|role|должность|вакансия):\s*", "", line)
                if title and len(title) > 3:
                    return title
            
            # First substantial line might be title (but not too long)
            if 5 < len(line) < 80:
                # Check if it looks like a title (not a bullet point, not all caps)
                if not line.startswith(("-", "•", "*", "—")):
                    if not line.isupper() or len(line.split()) <= 5:
                        return line
        
        return ""

    def _extract_company(self, text: str) -> Optional[str]:
        """Extract company name."""
        # Look for company patterns
        patterns = [
            r"(?i)company:\s*(.+)",
            r"(?i)employer:\s*(.+)",
            r"(?i)organization:\s*(.+)",
            r"(?i)работа в компании\s*(.+)",  # Russian: "работа в компании"
            r"(?i)компания:\s*(.+)",  # Russian: "компания:"
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                company = match.group(1).strip()
                # Clean up common suffixes
                company = re.sub(r"\s*\(.*?\)\s*$", "", company)  # Remove parentheses
                company = re.sub(r"\s*-\s*.*$", "", company)  # Remove after dash
                return company
        
        # Try to find company name in first few lines (common pattern)
        lines = text.split("\n")[:15]
        for line in lines:
            line = line.strip()
            # Look for lines that might contain company name
            if len(line) > 3 and len(line) < 100:
                # Check if it looks like a company name (not a title, not a requirement)
                if not re.search(r"(?i)^(position|title|job|requirements|responsibilities|qualifications)", line):
                    # Might be company name
                    if not re.search(r"[•\-\*]", line):  # Not a bullet point
                        return line
        
        return None

    def _extract_location(self, text: str) -> Optional[str]:
        """Extract location."""
        patterns = [
            r"(?i)location:\s*(.+)",
            r"(?i)city:\s*(.+)",
            r"(?i)address:\s*(.+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return None

    def _extract_requirements(self, text: str) -> List[str]:
        """Extract requirements section."""
        requirements = []
        # Look for requirements section
        req_section = self._extract_section(
            text, ["requirements", "qualifications", "must have", "required"]
        )
        if req_section:
            # Extract bullet points
            lines = req_section.split("\n")
            for line in lines[1:]:  # Skip header
                line = line.strip()
                if not line:
                    continue
                # Remove bullet markers
                line = re.sub(r"^[-•*]\s*", "", line)
                line = re.sub(r"^\d+[.)]\s*", "", line)
                if line:
                    requirements.append(line)
        return requirements

    def _extract_responsibilities(self, text: str) -> List[str]:
        """Extract responsibilities section."""
        responsibilities = []
        # Look for responsibilities section
        resp_section = self._extract_section(
            text,
            [
                "responsibilities",
                "duties",
                "what you'll do",
                "key responsibilities",
            ],
        )
        if resp_section:
            # Extract bullet points
            lines = resp_section.split("\n")
            for line in lines[1:]:  # Skip header
                line = line.strip()
                if not line:
                    continue
                # Remove bullet markers
                line = re.sub(r"^[-•*]\s*", "", line)
                line = re.sub(r"^\d+[.)]\s*", "", line)
                if line:
                    responsibilities.append(line)
        return responsibilities

    def _extract_section(self, text: str, keywords: List[str]) -> Optional[str]:
        """Extract a section by keywords."""
        lines = text.split("\n")
        start_idx = None

        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            for keyword in keywords:
                if keyword in line_lower:
                    start_idx = i
                    break
            if start_idx is not None:
                break

        if start_idx is None:
            return None

        # Find end of section
        end_idx = len(lines)
        for i in range(start_idx + 1, len(lines)):
            line = lines[i].strip()
            if not line:
                continue
            # Check if this is another section header (all caps or has colon)
            if line.isupper() or ":" in line:
                if i > start_idx + 2:  # At least a few lines
                    end_idx = i
                    break

        return "\n".join(lines[start_idx:end_idx])

    def _categorize_keywords(
        self, keywords: List[str], requirements: List[str], text: str
    ) -> tuple[List[str], List[str]]:
        """Categorize keywords into must-have and nice-to-have."""
        must_have = []
        nice_to_have = []

        # Keywords in requirements are must-have
        req_text = " ".join(requirements).lower()
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in req_text:
                must_have.append(keyword)
            else:
                nice_to_have.append(keyword)

        return must_have, nice_to_have

