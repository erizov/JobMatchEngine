"""Enhance resume by adding keywords while preserving structure."""

import re
from typing import List, Optional

from app.generators.llm_client import LLMClient
from app.models import Experience, JobPosting, ParsedResume
from app.utils.llm_cache import llm_cache


class ResumeEnhancer:
    """
    Enhance resume by adding keywords while preserving all structure.
    
    Unlike ResumeGenerator which rewrites sections, this class enhances
    existing content by naturally incorporating keywords from job postings.
    """

    def __init__(self):
        """Initialize enhancer."""
        self.llm = LLMClient()

    def enhance_resume(
        self,
        resume: ParsedResume,
        job: JobPosting,
        tone: str = "balanced",
        rag_context: Optional[str] = None,
    ) -> ParsedResume:
        """
        Enhance resume by adding keywords while preserving all structure.

        Args:
            resume: Original parsed resume
            job: Job posting with keywords
            tone: Enhancement tone (conservative, balanced, aggressive)
            rag_context: Optional RAG knowledge base context

        Returns:
            Enhanced ParsedResume with all original sections preserved
        """
        # Detect if we need to translate (English source -> Russian target)
        source_lang = self._detect_content_language(resume)
        target_lang = resume.language or "en"
        needs_translation = (source_lang == "en" and target_lang == "ru")
        
        # Enhance summary by adding keywords to existing text
        # If no summary exists, create one from experience and skills
        if not resume.summary:
            enhanced_summary = self._create_summary_from_experience(
                resume, job, tone, rag_context
            )
        else:
            enhanced_summary = self._enhance_summary(
                resume.summary, resume, job, tone, rag_context
            )
            
        # Translate summary if needed
        if needs_translation and enhanced_summary:
            enhanced_summary = self._translate_text(enhanced_summary, "ru")

        # Enhance experience bullets by adding keywords
        enhanced_experience = self._enhance_experience(
            resume.experience, resume, job, tone, rag_context
        )
        
        # Translate experience if needed
        if needs_translation:
            enhanced_experience = self._translate_experience(enhanced_experience, "ru")

        # Enhance skills by adding relevant keywords
        enhanced_skills = self._enhance_skills(
            resume.skills, resume, job, tone, rag_context
        )
        
        # Translate skills if needed
        if needs_translation:
            enhanced_skills = self._translate_skills(enhanced_skills, "ru")

        # Create enhanced resume - preserve ALL original sections
        enhanced_resume = ParsedResume(
            contact=resume.contact,  # Never change contact info
            summary=enhanced_summary or resume.summary,
            experience=enhanced_experience or resume.experience,
            skills=enhanced_skills or resume.skills,
            education=resume.education,  # Preserve as-is
            certifications=resume.certifications,  # Preserve as-is
            languages=resume.languages,  # Preserve as-is
            language=resume.language,  # Preserve language
            raw_text=resume.raw_text,  # Keep original raw text
        )

        return enhanced_resume

    def _enhance_summary(
        self,
        original_summary: Optional[str],
        resume: ParsedResume,
        job: JobPosting,
        tone: str,
        rag_context: Optional[str] = None,
    ) -> Optional[str]:
        """
        Enhance summary by adding keywords naturally to existing text.

        Preserves original content and structure, just adds keywords.
        """
        if not original_summary:
            return None

        target_language = resume.language or "en"
        keywords = job.must_have_keywords[:10]

        # Build enhancement prompt
        rag_section = ""
        if rag_context:
            rag_section = f"""
Additional Context (Knowledge Base):
{rag_context[:2000]}

"""

        tone_instruction = self._get_tone_instruction(tone)

        prompt = f"""You are a professional resume enhancer. Enhance the existing resume summary by naturally incorporating relevant keywords from the job posting.

CRITICAL: Preserve ALL original content, structure, and meaning. Only ADD keywords naturally - do NOT rewrite or remove anything.

{rag_section}Job Title: {job.title}
Relevant Keywords: {', '.join(keywords)}

Original Summary:
{original_summary}

{tone_instruction}

Instructions:
1. Keep ALL original text and meaning
2. Add relevant keywords from the job posting naturally into the existing text
3. Do NOT remove or change existing content
4. Do NOT rewrite sentences - only enhance them with keywords
5. Maintain the same structure and flow
6. Write COMPLETELY in {target_language.upper()} language
7. If keywords don't fit naturally, add them at the end in a new sentence
8. Preserve all facts, numbers, and specific details

Enhanced summary (preserve original + add keywords):"""

        system_prompt = (
            "You are a professional resume enhancer. Your job is to enhance "
            "existing resume content by naturally adding keywords, NOT rewriting it."
        )

        if target_language == "ru":
            system_prompt = (
                "Вы профессиональный оптимизатор резюме. Ваша задача - улучшить "
                "существующий текст резюме, естественно добавляя ключевые слова, "
                "НЕ переписывая его. Пишите ПОЛНОСТЬЮ на русском языке."
            )

        try:
            # Check cache
            cached_response = llm_cache.get(prompt, system_prompt)
            if cached_response:
                # Verify language
                if target_language == "ru":
                    russian_chars = sum(
                        1 for c in cached_response if '\u0400' <= c <= '\u04FF'
                    )
                    if russian_chars < len(cached_response) * 0.3:
                        cached_response = None

                if cached_response:
                    from app.utils.token_tracker import token_tracker
                    token_tracker.add_usage(cached=True)
                    return cached_response.strip()

            if not cached_response:
                enhanced = self.llm.generate(
                    prompt,
                    system_prompt=system_prompt,
                    temperature=0.5,  # Lower temperature for more conservative enhancement
                    max_tokens=400,
                )
                if enhanced:
                    llm_cache.set(prompt, enhanced, system_prompt)
                    return enhanced.strip()

            return original_summary
        except Exception as e:
            print(f"Warning: Summary enhancement failed: {e}")
            return original_summary

    def _create_summary_from_experience(
        self,
        resume: ParsedResume,
        job: JobPosting,
        tone: str,
        rag_context: Optional[str] = None,
    ) -> Optional[str]:
        """
        Create a summary from experience and skills when none exists.
        
        This preserves the structure by ensuring a summary section exists.
        """
        target_language = resume.language or "en"
        keywords = job.must_have_keywords[:10]

        # Build summary from experience entries
        experience_summary = []
        if resume.experience:
            for exp in resume.experience[:3]:  # Use first 3 experiences
                if exp.title and len(exp.title) > 20:
                    experience_summary.append(exp.title)
        
        # Combine with skills
        skills_text = ", ".join(resume.skills[:10]) if resume.skills else ""
        
        rag_section = ""
        if rag_context:
            rag_section = f"""
Additional Context (Knowledge Base):
{rag_context[:2000]}

"""

        prompt = f"""Create a professional resume summary from the candidate's experience and skills.

CRITICAL: Use ONLY the actual information provided. DO NOT invent facts.

{rag_section}Job Title: {job.title}
Relevant Keywords: {', '.join(keywords)}

Candidate Experience:
{chr(10).join(experience_summary[:3]) if experience_summary else 'No specific experience provided'}

Candidate Skills:
{skills_text if skills_text else 'No skills listed'}

Instructions:
1. Create a 4-6 sentence professional summary (80-120 words)
2. Highlight relevant experience and skills that match the job
3. Include key keywords from job requirements naturally
4. Maintain professional tone
5. DO NOT invent facts, companies, or experiences
6. Write COMPLETELY in {target_language.upper()} language
7. Be specific about years of experience, key technologies, and achievements

Generate the professional summary:"""

        system_prompt = (
            "You are a professional resume writer. Create a professional summary "
            "from the candidate's actual experience and skills."
        )

        if target_language == "ru":
            system_prompt = (
                "Вы профессиональный писатель резюме. Создайте профессиональное "
                "резюме на основе фактического опыта и навыков кандидата. "
                "Пишите ПОЛНОСТЬЮ на русском языке."
            )

        try:
            # Check cache
            cached_response = llm_cache.get(prompt, system_prompt)
            if cached_response:
                if target_language == "ru":
                    russian_chars = sum(
                        1 for c in cached_response if '\u0400' <= c <= '\u04FF'
                    )
                    if russian_chars < len(cached_response) * 0.3:
                        cached_response = None

                if cached_response:
                    from app.utils.token_tracker import token_tracker
                    token_tracker.add_usage(cached=True)
                    return cached_response.strip()

            if not cached_response:
                summary = self.llm.generate(
                    prompt,
                    system_prompt=system_prompt,
                    temperature=0.7,
                    max_tokens=400,
                )
                if summary:
                    llm_cache.set(prompt, summary, system_prompt)
                    # Clean up response
                    summary = summary.strip()
                    import re
                    summary = re.sub(r"```[\w]*\n?", "", summary)
                    summary = re.sub(r"```", "", summary)
                    summary = summary.strip()
                    return summary

            return None
        except Exception as e:
            print(f"Warning: Summary creation failed: {e}")
            return None

    def _enhance_experience(
        self,
        original_experience: List[Experience],
        resume: ParsedResume,
        job: JobPosting,
        tone: str,
        rag_context: Optional[str] = None,
    ) -> List[Experience]:
        """
        Enhance experience bullets by adding keywords to existing text.

        Preserves all original bullets, just enhances them with keywords.
        """
        if not original_experience:
            return original_experience

        target_language = resume.language or "en"
        keywords = job.must_have_keywords[:15]
        enhanced_experience = []

        for exp in original_experience:
            if not exp.bullets:
                # Keep experience entry even without bullets
                enhanced_experience.append(exp)
                continue

            # Enhance each bullet point
            enhanced_bullets = []
            for bullet in exp.bullets:
                enhanced_bullet = self._enhance_bullet(
                    bullet, exp, job, keywords, target_language, rag_context
                )
                enhanced_bullets.append(enhanced_bullet)

            # Create enhanced experience entry
            enhanced_exp = Experience(
                title=exp.title,  # Preserve title
                company=exp.company,  # Preserve company
                dates=exp.dates,  # Preserve dates
                location=exp.location,  # Preserve location
                bullets=enhanced_bullets if enhanced_bullets else exp.bullets,
                raw_text=exp.raw_text,  # Preserve raw text
            )
            enhanced_experience.append(enhanced_exp)

        return enhanced_experience

    def _enhance_bullet(
        self,
        original_bullet: str,
        experience: Experience,
        job: JobPosting,
        keywords: List[str],
        target_language: str,
        rag_context: Optional[str] = None,
    ) -> str:
        """Enhance a single bullet point by adding keywords naturally."""
        if not original_bullet or len(original_bullet.strip()) < 10:
            return original_bullet

        # Find relevant keywords for this bullet
        relevant_keywords = self._find_relevant_keywords(
            original_bullet, keywords, job
        )

        if not relevant_keywords:
            return original_bullet  # No relevant keywords, keep as-is

        rag_section = ""
        if rag_context:
            rag_section = f"""
Additional Context (Knowledge Base):
{rag_context[:1000]}

"""

        prompt = f"""Enhance this resume bullet point by naturally adding relevant keywords.

CRITICAL: Keep ALL original content and meaning. Only ADD keywords - do NOT rewrite.

{rag_section}Job Title: {job.title}
Relevant Keywords: {', '.join(relevant_keywords[:5])}

Original Bullet:
{original_bullet}

Job Title: {experience.title}
Company: {experience.company}

Instructions:
1. Keep ALL original text and meaning
2. Add 1-2 relevant keywords naturally into the existing sentence
3. Do NOT remove or change existing content
4. Do NOT rewrite the sentence - only enhance it
5. Maintain the same structure and flow
6. Write COMPLETELY in {target_language.upper()} language
7. If keywords don't fit naturally, skip adding them

Enhanced bullet (preserve original + add keywords if natural):"""

        system_prompt = (
            "You are a professional resume enhancer. Enhance existing "
            "bullet points by naturally adding keywords, NOT rewriting them."
        )

        if target_language == "ru":
            system_prompt = (
                "Вы профессиональный оптимизатор резюме. Улучшайте существующие "
                "пункты опыта, естественно добавляя ключевые слова, НЕ переписывая их. "
                "Пишите ПОЛНОСТЬЮ на русском языке."
            )

        try:
            # Check cache
            cached_response = llm_cache.get(prompt, system_prompt)
            if cached_response:
                if target_language == "ru":
                    russian_chars = sum(
                        1 for c in cached_response if '\u0400' <= c <= '\u04FF'
                    )
                    if russian_chars < len(cached_response) * 0.3:
                        cached_response = None

                if cached_response:
                    from app.utils.token_tracker import token_tracker
                    token_tracker.add_usage(cached=True)
                    enhanced = cached_response.strip()
                    # Remove markdown formatting
                    enhanced = re.sub(r"^[-•*]\s*", "", enhanced)
                    enhanced = re.sub(r"```[\w]*\n?", "", enhanced)
                    return enhanced if enhanced else original_bullet

            if not cached_response:
                enhanced = self.llm.generate(
                    prompt,
                    system_prompt=system_prompt,
                    temperature=0.4,  # Very conservative
                    max_tokens=150,
                )
                if enhanced:
                    llm_cache.set(prompt, enhanced, system_prompt)
                    enhanced = enhanced.strip()
                    # Remove markdown formatting
                    enhanced = re.sub(r"^[-•*]\s*", "", enhanced)
                    enhanced = re.sub(r"```[\w]*\n?", "", enhanced)
                    return enhanced if enhanced else original_bullet

            return original_bullet
        except Exception as e:
            print(f"Warning: Bullet enhancement failed: {e}")
            return original_bullet

    def _enhance_skills(
        self,
        original_skills: List[str],
        resume: ParsedResume,
        job: JobPosting,
        tone: str,
        rag_context: Optional[str] = None,
    ) -> List[str]:
        """
        Enhance skills by adding relevant keywords.

        Preserves all original skills, adds relevant ones from job posting.
        """
        if not original_skills:
            return original_skills

        keywords = job.must_have_keywords + job.nice_to_have_keywords
        target_language = resume.language or "en"

        # Find skills that are already in the resume
        existing_skills_lower = [s.lower().strip() for s in original_skills]

        # Find relevant keywords that aren't already in skills
        new_skills = []
        for keyword in keywords[:20]:  # Limit to top 20 keywords
            keyword_lower = keyword.lower().strip()
            # Check if keyword or similar is already in skills
            if any(
                keyword_lower in skill or skill in keyword_lower
                for skill in existing_skills_lower
            ):
                continue

            # Check if keyword is relevant to existing skills
            if self._is_skill_relevant(keyword, original_skills, job):
                new_skills.append(keyword)

        # Add up to 3-5 new relevant skills based on tone
        max_additions = {"conservative": 2, "balanced": 3, "aggressive": 5}.get(
            tone, 3
        )

        # Combine original skills with new ones
        enhanced_skills = list(original_skills)  # Preserve all original
        enhanced_skills.extend(new_skills[:max_additions])

        return enhanced_skills

    def _find_relevant_keywords(
        self, text: str, keywords: List[str], job: JobPosting
    ) -> List[str]:
        """Find keywords relevant to the given text."""
        text_lower = text.lower()
        relevant = []

        for keyword in keywords:
            keyword_lower = keyword.lower()
            # Check if keyword is related to the text content
            if keyword_lower in text_lower:
                continue  # Already present

            # Simple relevance check: keyword should relate to tech/domain
            if any(
                word in keyword_lower
                for word in text_lower.split()
                if len(word) > 4
            ):
                relevant.append(keyword)

        return relevant[:5]  # Return top 5 relevant keywords

    def _is_skill_relevant(
        self, keyword: str, existing_skills: List[str], job: JobPosting
    ) -> bool:
        """Check if a keyword is relevant to add as a skill."""
        keyword_lower = keyword.lower()

        # Check if it's a technical term (common patterns)
        tech_patterns = [
            r"\w+\s*(framework|library|tool|language|platform|api|sdk)",
            r"(python|java|javascript|typescript|sql|html|css|react|vue|angular)",
            r"(docker|kubernetes|aws|azure|gcp|ci/cd|git|jenkins)",
        ]

        for pattern in tech_patterns:
            if re.search(pattern, keyword_lower, re.IGNORECASE):
                return True

        # Check if it's related to existing skills
        for skill in existing_skills:
            skill_words = set(skill.lower().split())
            keyword_words = set(keyword_lower.split())
            if skill_words.intersection(keyword_words):
                return True

        return False

    def _get_tone_instruction(self, tone: str) -> str:
        """Get instruction based on enhancement tone."""
        instructions = {
            "conservative": (
                "Enhancement style: Very conservative. Only add keywords that "
                "fit naturally. Preserve original content exactly."
            ),
            "balanced": (
                "Enhancement style: Balanced. Add keywords naturally where "
                "they fit. Preserve original content and meaning."
            ),
            "aggressive": (
                "Enhancement style: More aggressive. Add more keywords, but "
                "still preserve original content and meaning."
            ),
        }
        return instructions.get(tone, instructions["balanced"])

    def _detect_content_language(self, resume: ParsedResume) -> str:
        """Detect the actual language of resume content."""
        # Check experience titles and bullets for language
        if resume.experience:
            for exp in resume.experience[:2]:
                if exp.title:
                    # Check for Cyrillic characters
                    has_cyrillic = any('\u0400' <= c <= '\u04FF' for c in exp.title)
                    if has_cyrillic:
                        return "ru"
                if exp.bullets:
                    bullet_text = " ".join(exp.bullets[:2])
                    has_cyrillic = any('\u0400' <= c <= '\u04FF' for c in bullet_text)
                    if has_cyrillic:
                        return "ru"
        
        # Check skills
        if resume.skills:
            skills_text = " ".join(resume.skills[:5])
            has_cyrillic = any('\u0400' <= c <= '\u04FF' for c in skills_text)
            if has_cyrillic:
                return "ru"
        
        # Default to English if no Cyrillic found
        return "en"

    def _translate_text(self, text: str, target_lang: str) -> str:
        """Translate text to target language."""
        if not text or len(text) < 5:
            return text
            
        prompt = f"""Translate the following text to {target_lang.upper()} language.

CRITICAL: Translate accurately while preserving meaning and tone.

Original text:
{text}

Instructions:
1. Translate to {target_lang.upper()} language
2. Preserve professional tone
3. Keep the same meaning and structure
4. Use appropriate terminology
5. Natural, fluent translation

Translated text:"""

        system_prompt = (
            "You are a professional translator. Translate accurately "
            "while preserving meaning and tone."
        )

        if target_lang == "ru":
            system_prompt = (
                "Вы профессиональный переводчик. Переводите точно, "
                "сохраняя смысл и тон. Пишите ПОЛНОСТЬЮ на русском языке."
            )

        try:
            translated = self.llm.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.3,  # Lower temperature for accurate translation
                max_tokens=len(text) * 3,  # Allow space for translation
            )
            if translated:
                return translated.strip()
            return text
        except Exception as e:
            print(f"Warning: Translation failed: {e}")
            return text

    def _translate_experience(
        self, experiences: List[Experience], target_lang: str
    ) -> List[Experience]:
        """Translate experience entries to target language."""
        translated_experiences = []
        
        for exp in experiences:
            # Translate title
            translated_title = self._translate_text(exp.title, target_lang) if exp.title else exp.title
            
            # Translate bullets
            translated_bullets = []
            for bullet in exp.bullets:
                translated_bullet = self._translate_text(bullet, target_lang)
                translated_bullets.append(translated_bullet)
            
            # Create translated experience entry
            translated_exp = Experience(
                title=translated_title,
                company=exp.company,  # Keep company name as-is
                dates=exp.dates,  # Keep dates as-is
                location=exp.location,  # Keep location as-is
                bullets=translated_bullets,
                raw_text=exp.raw_text,
            )
            translated_experiences.append(translated_exp)
        
        return translated_experiences

    def _translate_skills(self, skills: List[str], target_lang: str) -> List[str]:
        """Translate skills to target language."""
        if not skills:
            return skills
            
        # Translate skills as a batch for efficiency
        skills_text = ", ".join(skills)
        
        prompt = f"""Translate the following technical skills to {target_lang.upper()} language.

CRITICAL: Translate technical terms appropriately for {target_lang.upper()}.

Original skills:
{skills_text}

Instructions:
1. Translate to {target_lang.upper()} language
2. Keep technology names in original form when appropriate (e.g., Python, Docker, AWS)
3. Translate descriptive terms (e.g., "Web Development" -> "Веб-разработка")
4. Return as comma-separated list
5. Preserve all skills

Translated skills (comma-separated):"""

        system_prompt = (
            "You are a professional translator specializing in technical terminology. "
            "Translate accurately while keeping technology names recognizable."
        )

        if target_lang == "ru":
            system_prompt = (
                "Вы профессиональный переводчик технической терминологии. "
                "Переводите точно, сохраняя узнаваемость названий технологий."
            )

        try:
            translated = self.llm.generate(
                prompt,
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=len(skills_text) * 2,
            )
            if translated:
                # Parse translated skills
                translated_skills = [s.strip() for s in translated.split(",")]
                return translated_skills if translated_skills else skills
            return skills
        except Exception as e:
            print(f"Warning: Skills translation failed: {e}")
            return skills

