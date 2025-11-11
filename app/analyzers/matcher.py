"""Match resume against job posting and compute ATS score."""

from typing import List, Set

from app.models import JobPosting, MatchAnalysis, ParsedResume


class ResumeMatcher:
    """Match resume against job posting."""

    def __init__(self):
        """Initialize matcher."""
        pass

    def analyze_match(
        self, resume: ParsedResume, job: JobPosting
    ) -> MatchAnalysis:
        """
        Analyze how well resume matches job posting.

        Args:
            resume: Parsed resume
            job: Job posting

        Returns:
            MatchAnalysis with scores and recommendations
        """
        # Extract all keywords from resume
        resume_keywords = self._extract_resume_keywords(resume)

        # Get job keywords
        job_keywords = set(
            job.keywords + job.must_have_keywords + job.nice_to_have_keywords
        )
        must_have = set(job.must_have_keywords)
        nice_to_have = set(job.nice_to_have_keywords)

        # Compute overlap
        resume_keywords_set = set(kw.lower() for kw in resume_keywords)
        job_keywords_lower = set(kw.lower() for kw in job_keywords)
        must_have_lower = set(kw.lower() for kw in must_have)
        nice_to_have_lower = set(kw.lower() for kw in nice_to_have)

        overlap = resume_keywords_set & job_keywords_lower
        missing_must_have = must_have_lower - resume_keywords_set
        missing_nice_to_have = nice_to_have_lower - resume_keywords_set

        # Compute ATS score
        ats_score = self._compute_ats_score(
            resume_keywords_set,
            job_keywords_lower,
            must_have_lower,
            nice_to_have_lower,
            resume,
            job,
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            missing_must_have, missing_nice_to_have, resume, job
        )

        return MatchAnalysis(
            ats_score=ats_score,
            keyword_overlap=list(overlap),
            missing_keywords=list(missing_must_have | missing_nice_to_have),
            recommendations=recommendations,
        )

    def _extract_resume_keywords(self, resume: ParsedResume) -> List[str]:
        """Extract all keywords from resume."""
        keywords = []

        # Add skills
        keywords.extend(resume.skills)

        # Add keywords from summary
        if resume.summary:
            # Simple extraction: words in summary
            words = resume.summary.lower().split()
            keywords.extend(words)

        # Add keywords from experience
        for exp in resume.experience:
            keywords.append(exp.title.lower())
            keywords.append(exp.company.lower())
            for bullet in exp.bullets:
                words = bullet.lower().split()
                keywords.extend(words)

        return keywords

    def _compute_ats_score(
        self,
        resume_keywords: Set[str],
        job_keywords: Set[str],
        must_have: Set[str],
        nice_to_have: Set[str],
        resume: ParsedResume,
        job: JobPosting,
    ) -> float:
        """
        Compute ATS compatibility score (0-100).

        Args:
            resume_keywords: Set of keywords in resume (lowercase)
            job_keywords: Set of keywords in job posting (lowercase)
            must_have: Set of must-have keywords (lowercase)
            nice_to_have: Set of nice-to-have keywords (lowercase)
            resume: Parsed resume
            job: Job posting

        Returns:
            ATS score (0-100)
        """
        if not job_keywords:
            return 50.0  # Default score if no keywords

        # Keyword match score (60% weight)
        overlap = resume_keywords & job_keywords
        keyword_match_ratio = len(overlap) / len(job_keywords) if job_keywords else 0
        keyword_score = keyword_match_ratio * 60

        # Must-have keywords score (30% weight)
        must_have_match = resume_keywords & must_have
        must_have_ratio = (
            len(must_have_match) / len(must_have) if must_have else 1.0
        )
        must_have_score = must_have_ratio * 30

        # Title match score (10% weight)
        title_score = 0.0
        if job.title:
            job_title_lower = job.title.lower()
            # Check if job title appears in resume
            resume_text_lower = resume.raw_text.lower()
            if job_title_lower in resume_text_lower:
                title_score = 10.0
            else:
                # Check for partial match
                title_words = set(job_title_lower.split())
                resume_words = set(resume_text_lower.split())
                if title_words & resume_words:
                    title_score = 5.0

        total_score = keyword_score + must_have_score + title_score
        return min(100.0, max(0.0, total_score))

    def _generate_recommendations(
        self,
        missing_must_have: Set[str],
        missing_nice_to_have: Set[str],
        resume: ParsedResume,
        job: JobPosting,
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        if missing_must_have:
            recommendations.append(
                f"Add must-have keywords: {', '.join(list(missing_must_have)[:5])}"
            )

        if missing_nice_to_have:
            recommendations.append(
                f"Consider adding: {', '.join(list(missing_nice_to_have)[:5])}"
            )

        # Check if summary exists and is relevant
        if not resume.summary or len(resume.summary) < 50:
            recommendations.append(
                "Add a professional summary section highlighting "
                "key qualifications"
            )

        # Check skills section
        if not resume.skills or len(resume.skills) < 5:
            recommendations.append("Expand skills section with relevant keywords")

        return recommendations

