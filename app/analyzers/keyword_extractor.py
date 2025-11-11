"""Keyword extraction from resumes and job postings."""

from typing import List, Set

try:
    from keybert import KeyBERT
except ImportError:
    KeyBERT = None

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
except ImportError:
    TfidfVectorizer = None


class KeywordExtractor:
    """Extract keywords from text using TF-IDF and KeyBERT."""

    def __init__(self, use_keybert: bool = False):
        """
        Initialize keyword extractor.

        Args:
            use_keybert: Whether to use KeyBERT (requires sentence-transformers)
        """
        self.use_keybert = use_keybert and KeyBERT is not None
        if self.use_keybert:
            try:
                self.keybert_model = KeyBERT()
            except Exception:
                self.use_keybert = False
                self.keybert_model = None

        if TfidfVectorizer is not None:
            self.tfidf = TfidfVectorizer(
                max_features=100,
                ngram_range=(1, 2),
                stop_words="english",
                min_df=1,
            )
        else:
            self.tfidf = None

    def extract_keywords(
        self, text: str, top_k: int = 20, language: str = "en"
    ) -> List[str]:
        """
        Extract keywords from text.

        Args:
            text: Text to extract keywords from
            top_k: Number of keywords to return
            language: Language code ('ru' or 'en')

        Returns:
            List of keywords
        """
        if not text or len(text.strip()) < 10:
            return []

        # Clean text
        text = self._clean_text(text)

        keywords = []

        # Use KeyBERT if available
        if self.use_keybert:
            try:
                keybert_keywords = self.keybert_model.extract_keywords(
                    text, keyphrase_ngram_range=(1, 2), top_n=top_k
                )
                keywords.extend([kw[0] for kw in keybert_keywords])
            except Exception:
                pass

        # Use TF-IDF as fallback or supplement
        if TfidfVectorizer is not None:
            try:
                # Adjust stop words based on language
                if language == "ru":
                    # For Russian, we'd need Russian stop words
                    # For now, use minimal stop words
                    tfidf = TfidfVectorizer(
                        max_features=top_k,
                        ngram_range=(1, 2),
                        min_df=1,
                    )
                else:
                    tfidf = TfidfVectorizer(
                        max_features=top_k,
                        ngram_range=(1, 2),
                        stop_words="english",
                        min_df=1,
                    )

                tfidf_matrix = tfidf.fit_transform([text])
                feature_names = tfidf.get_feature_names_out()
                scores = tfidf_matrix.toarray()[0]

                # Get top keywords
                top_indices = scores.argsort()[-top_k:][::-1]
                tfidf_keywords = [feature_names[i] for i in top_indices if scores[i] > 0]

                keywords.extend(tfidf_keywords)
            except Exception:
                pass

        # Deduplicate and clean
        keywords = self._deduplicate_keywords(keywords)
        return keywords[:top_k]

    def extract_skills_keywords(self, skills: List[str]) -> List[str]:
        """
        Extract keywords from skills list.

        Args:
            skills: List of skills

        Returns:
            List of skill keywords
        """
        if not skills:
            return []

        # Normalize skills
        normalized = []
        for skill in skills:
            # Split by common separators
            parts = skill.replace(",", " ").replace("|", " ").split()
            normalized.extend([p.strip() for p in parts if p.strip()])

        return list(dict.fromkeys(normalized))  # Preserve order, remove duplicates

    def _clean_text(self, text: str) -> str:
        """Clean text for keyword extraction."""
        # Remove extra whitespace
        text = " ".join(text.split())
        # Remove special characters but keep spaces and basic punctuation
        import re

        text = re.sub(r"[^\w\s-]", " ", text)
        return text

    def _deduplicate_keywords(self, keywords: List[str]) -> List[str]:
        """Remove duplicate and similar keywords."""
        seen: Set[str] = set()
        result = []

        for keyword in keywords:
            keyword_lower = keyword.lower().strip()
            if not keyword_lower:
                continue

            # Check if similar keyword already exists
            is_duplicate = False
            for seen_keyword in seen:
                if (
                    keyword_lower == seen_keyword.lower()
                    or keyword_lower in seen_keyword.lower()
                    or seen_keyword.lower() in keyword_lower
                ):
                    is_duplicate = True
                    break

            if not is_duplicate:
                seen.add(keyword_lower)
                result.append(keyword)

        return result

