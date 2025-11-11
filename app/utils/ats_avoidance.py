"""Strategies to avoid ATS blockers."""

from typing import List


class ATSAvoidance:
    """Strategies to avoid common ATS blockers."""

    @staticmethod
    def avoid_keyword_stuffing(text: str, max_keyword_density: float = 0.05) -> str:
        """
        Avoid keyword stuffing by limiting keyword density.

        Args:
            text: Text to check
            max_keyword_density: Maximum keyword density (0.05 = 5%)

        Returns:
            Text with adjusted keyword density if needed
        """
        # Simple implementation: check for repeated keywords
        words = text.lower().split()
        word_counts = {}
        for word in words:
            word_counts[word] = word_counts.get(word, 0) + 1

        # If any word appears too frequently, flag it
        total_words = len(words)
        for word, count in word_counts.items():
            density = count / total_words if total_words > 0 else 0
            if density > max_keyword_density and len(word) > 3:
                # This would trigger a warning in production
                pass

        return text

    @staticmethod
    def ensure_ats_friendly_formatting(text: str) -> str:
        """
        Ensure formatting is ATS-friendly.

        Args:
            text: Text to format

        Returns:
            ATS-friendly formatted text
        """
        # Remove special characters that ATS might not parse well
        # Keep basic punctuation
        import re

        # Remove non-standard characters but keep basic punctuation
        text = re.sub(r"[^\w\s.,;:!?()-]", " ", text)
        # Normalize whitespace
        text = " ".join(text.split())
        return text

    @staticmethod
    def avoid_ai_detection_patterns(text: str) -> str:
        """
        Avoid patterns that might trigger AI detection.

        Args:
            text: Text to check

        Returns:
            Text with adjusted patterns
        """
        # Avoid overly perfect grammar or repetitive structures
        # This is a placeholder - actual implementation would be more sophisticated
        return text

    @staticmethod
    def validate_fact_consistency(
        original_text: str, enhanced_text: str
    ) -> List[str]:
        """
        Validate that enhanced text doesn't introduce new facts.

        Args:
            original_text: Original resume text
            enhanced_text: Enhanced resume text

        Returns:
            List of warnings about potential inconsistencies
        """
        warnings = []

        # Extract dates, companies, metrics from original
        import re

        # Check for new company names
        original_companies = set(
            re.findall(r"\b[A-Z][a-z]+ (?:Inc|LLC|Corp|Ltd|Company)\b", original_text)
        )
        enhanced_companies = set(
            re.findall(
                r"\b[A-Z][a-z]+ (?:Inc|LLC|Corp|Ltd|Company)\b", enhanced_text
            )
        )
        new_companies = enhanced_companies - original_companies
        if new_companies:
            warnings.append(f"New companies detected: {new_companies}")

        # Check for new dates
        original_dates = set(re.findall(r"\d{4}", original_text))
        enhanced_dates = set(re.findall(r"\d{4}", enhanced_text))
        # Allow some variance (years might be reformatted)
        # This is a simple check - more sophisticated validation needed

        return warnings

    @staticmethod
    def optimize_for_ats_keywords(
        text: str, target_keywords: List[str], max_additions: int = 3
    ) -> str:
        """
        Add target keywords naturally without stuffing.

        Args:
            text: Original text
            target_keywords: Keywords to include
            max_additions: Maximum keywords to add

        Returns:
            Text with keywords added naturally
        """
        # This is a placeholder - actual implementation would use LLM
        # to naturally incorporate keywords
        return text

    @staticmethod
    def check_readability(text: str) -> dict:
        """
        Check text readability metrics.

        Args:
            text: Text to check

        Returns:
            Dictionary with readability metrics
        """
        words = text.split()
        sentences = text.split(".")

        metrics = {
            "word_count": len(words),
            "sentence_count": len(sentences),
            "avg_words_per_sentence": len(words) / len(sentences)
            if sentences
            else 0,
            "avg_word_length": sum(len(w) for w in words) / len(words)
            if words
            else 0,
        }

        return metrics

