"""Language detection for resumes and job postings."""

from typing import Optional

try:
    from langdetect import detect, DetectorFactory, LangDetectException
except ImportError:
    detect = None
    DetectorFactory = None
    LangDetectException = Exception


class LanguageDetector:
    """Detect language of text (Russian/English)."""

    def __init__(self):
        """Initialize language detector."""
        if DetectorFactory is not None:
            # Set seed for reproducibility
            DetectorFactory.seed = 0

    def detect_language(self, text: str) -> str:
        """
        Detect language of text.

        Args:
            text: Text to analyze

        Returns:
            Language code: 'ru' for Russian, 'en' for English, 'unknown' otherwise
        """
        if detect is None:
            # Fallback: simple heuristic
            return self._heuristic_detect(text)

        if not text or len(text.strip()) < 10:
            return "en"  # Default to English for very short text

        try:
            lang_code = detect(text)
            # Map common codes to our codes
            if lang_code in ["ru", "uk", "be"]:
                return "ru"
            elif lang_code in ["en"]:
                return "en"
            else:
                # Default to English for unknown languages
                return "en"
        except LangDetectException:
            return self._heuristic_detect(text)

    def _heuristic_detect(self, text: str) -> str:
        """
        Fallback heuristic detection using Cyrillic characters.

        Args:
            text: Text to analyze

        Returns:
            Language code
        """
        if not text:
            return "en"

        # Count Cyrillic characters
        cyrillic_count = sum(1 for char in text if "\u0400" <= char <= "\u04FF")
        total_chars = sum(1 for char in text if char.isalpha())

        if total_chars == 0:
            return "en"

        cyrillic_ratio = cyrillic_count / total_chars

        # If more than 30% Cyrillic, likely Russian
        if cyrillic_ratio > 0.3:
            return "ru"
        else:
            return "en"

    def decide_output_language(
        self, resume_lang: str, job_lang: str, prefer_job: bool = True
    ) -> str:
        """
        Decide output language based on resume and job posting languages.

        Args:
            resume_lang: Language of resume ('ru' or 'en')
            job_lang: Language of job posting ('ru' or 'en')
            prefer_job: If True, prefer job posting language

        Returns:
            Output language code
        """
        if resume_lang == job_lang:
            return resume_lang

        if prefer_job:
            return job_lang
        else:
            return resume_lang

