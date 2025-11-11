"""Generate enhanced resume sections."""

import re
from typing import List, Optional

from app.generators.llm_client import LLMClient
from app.generators.prompt_builder import PromptBuilder
from app.models import Experience, JobPosting, ParsedResume
from app.utils.llm_cache import llm_cache


class ResumeGenerator:
    """Generate enhanced resume sections."""

    def __init__(self):
        """Initialize generator."""
        self.llm = LLMClient()
        self.prompt_builder = PromptBuilder()

    def generate_enhanced_resume(
        self,
        resume: ParsedResume,
        job: JobPosting,
        tone: str = "balanced",
        max_keywords: int = 3,
        rag_context: Optional[str] = None,
    ) -> ParsedResume:
        """
        Generate enhanced resume optimized for job posting.

        Args:
            resume: Original parsed resume
            job: Job posting
            tone: Generation tone
            max_keywords: Max keywords to add per section

        Returns:
            Enhanced ParsedResume
        """
        # Generate enhanced summary (fallback to original if fails)
        enhanced_summary = self.generate_summary(resume, job, tone, rag_context)
        if not enhanced_summary:
            enhanced_summary = resume.summary

        # Generate enhanced experience (fallback to original if fails or empty)
        enhanced_experience = self.generate_experience(resume, job, tone, rag_context)
        if not enhanced_experience:
            enhanced_experience = resume.experience

        # Generate enhanced skills (fallback to original if fails or empty)
        enhanced_skills = self.generate_skills(resume, job, max_keywords, rag_context)
        if not enhanced_skills:
            enhanced_skills = resume.skills

        # Create enhanced resume - always preserve original data
        enhanced_resume = ParsedResume(
            contact=resume.contact,
            summary=enhanced_summary or resume.summary,
            experience=enhanced_experience or resume.experience,
            skills=enhanced_skills or resume.skills,
            education=resume.education,
            certifications=resume.certifications,
            languages=resume.languages,
            language=resume.language,
            raw_text=resume.raw_text,  # Keep original raw text
        )

        return enhanced_resume

    def generate_summary(
        self,
        resume: ParsedResume,
        job: JobPosting,
        tone: str = "balanced",
        rag_context: Optional[str] = None,
    ) -> Optional[str]:
        """Generate enhanced summary."""
        prompt = self.prompt_builder.build_resume_summary_prompt(
            resume.summary, resume, job, tone, rag_context
        )

        system_prompt = (
            "You are a professional resume writer. Generate concise, "
            "professional summaries that are optimized for ATS systems while "
            "preserving all factual information."
        )

        try:
            # For language-specific generation, don't use cache if it's a different language
            # This ensures we get fresh Russian content, not cached English
            target_language = resume.language or "en"
            use_cache = True  # Can use cache if language matches
            
            cached_response = llm_cache.get(prompt, system_prompt) if use_cache else None
            if cached_response:
                # Check if cached response is in the correct language
                if target_language == "ru":
                    # If Russian, verify it's actually in Russian (not English)
                    russian_chars = sum(1 for c in cached_response if '\u0400' <= c <= '\u04FF')
                    if russian_chars < len(cached_response) * 0.3:  # Less than 30% Russian chars
                        cached_response = None  # Don't use English cached response for Russian
                
                if cached_response:
                    summary = cached_response
                    from app.utils.token_tracker import token_tracker
                    token_tracker.add_usage(cached=True)
            
            if not cached_response:
                summary = self.llm.generate(
                    prompt, 
                    system_prompt=system_prompt, 
                    temperature=0.7,
                    max_tokens=800  # Increased to allow comprehensive summary (80-120 words)
                )
                # Cache the response
                if summary:
                    llm_cache.set(prompt, summary, system_prompt)
            # Clean up response
            if summary:
                summary = summary.strip()
                # Remove quotes if present
                if summary.startswith('"') and summary.endswith('"'):
                    summary = summary[1:-1]
                # Remove markdown code blocks if present
                import re
                summary = re.sub(r"```[\w]*\n?", "", summary)
                summary = re.sub(r"```", "", summary)
                summary = summary.strip()
                
                # Check for error messages and skip them
                error_phrases = ["извините", "не могу", "cannot", "sorry", "unable", "error", "i apologize"]
                if any(phrase.lower() in summary.lower() for phrase in error_phrases):
                    print(f"Warning: Summary contains error message, using original")
                    return resume.summary
                    
            return summary if summary else resume.summary
        except Exception as e:
            # Fallback to original if generation fails
            print(f"Warning: Summary generation failed: {e}")
            return resume.summary

    def generate_experience(
        self,
        resume: ParsedResume,
        job: JobPosting,
        tone: str = "balanced",
        rag_context: Optional[str] = None,
    ) -> List[Experience]:
        """Generate enhanced experience entries."""
        enhanced_experience = []
        
        # Determine target language for prompts
        target_language = resume.language or "en"

        for exp in resume.experience:
            prompt = self.prompt_builder.build_experience_bullet_prompt(
                exp, job, tone, rag_context
            )
            
            # Add language-specific instruction to prompt
            if target_language == "ru":
                prompt += "\n\nCRITICAL: Write ALL bullets COMPLETELY in Russian language. Use Russian grammar, vocabulary, and technical terms. DO NOT use English words or phrases."
            else:
                prompt += "\n\nCRITICAL: Write ALL bullets COMPLETELY in English language. Use English grammar and vocabulary."

            # Language-specific system prompt
            if target_language == "ru":
                system_prompt = (
                    "Вы профессиональный писатель резюме. Оптимизируйте пункты опыта работы "
                    "для систем ATS, сохраняя все факты. ВАЖНО: Пишите ПОЛНОСТЬЮ на русском языке, "
                    "не смешивайте языки. Используйте русскую грамматику и технические термины на русском."
                )
            else:
                system_prompt = (
                    "You are a professional resume writer. Optimize experience "
                    "bullets for ATS compatibility while preserving all facts. "
                    "Write COMPLETELY in English language."
                )

            try:
                # For language-specific generation, check cache but verify language
                cached_response = llm_cache.get(prompt, system_prompt)
                if cached_response:
                    # Check if cached response is in the correct language
                    if target_language == "ru":
                        # If Russian, verify it's actually in Russian (not English)
                        russian_chars = sum(1 for c in cached_response if '\u0400' <= c <= '\u04FF')
                        if russian_chars < len(cached_response) * 0.3:  # Less than 30% Russian chars
                            cached_response = None  # Don't use English cached response for Russian
                    
                    if cached_response:
                        response = cached_response
                        from app.utils.token_tracker import token_tracker
                        token_tracker.add_usage(cached=True)
                
                if not cached_response:
                    response = self.llm.generate(
                        prompt, 
                        system_prompt=system_prompt, 
                        temperature=0.7,
                        max_tokens=1200  # Increased to allow full experience bullets with more detail
                    )
                    # Cache the response
                    if response:
                        llm_cache.set(prompt, response, system_prompt)

                # Check if response contains error messages
                if response and any(err in response.lower() for err in ["i apologize", "i cannot", "error", "sorry", "unable"]):
                    # If LLM returned an error, use original bullets
                    print(f"         [WARN] LLM returned error message for {exp.title}, using original bullets")
                    final_bullets = exp.bullets if exp.bullets else []
                else:
                    # Parse bullets from response
                    bullets = self._parse_bullets(response)
                    
                    # Ensure we have bullets - use original if LLM didn't generate any
                    final_bullets = bullets if bullets else (exp.bullets if exp.bullets else [])
                
                # If still no bullets, try to extract from raw_text
                if not final_bullets and exp.raw_text:
                    # Extract lines that look like bullets
                    lines = [line.strip() for line in exp.raw_text.split("\n") if line.strip()]
                    potential_bullets = []
                    for line in lines:
                        # Skip headers, dates, titles, error messages
                        if (len(line) > 15 and 
                            not any(skip in line.lower() for skip in ["title:", "company:", "dates:", "experience", "summary", "i apologize", "i cannot", "error", "sorry"])):
                            # Remove bullet markers
                            clean_line = line.lstrip("-•* ").strip()
                            if clean_line:
                                potential_bullets.append(clean_line)
                    if potential_bullets:
                        final_bullets = potential_bullets[:5]  # Limit to 5

                # Create enhanced experience entry - always include even if bullets are empty
                enhanced_exp = Experience(
                    title=exp.title,
                    company=exp.company,
                    dates=exp.dates,
                    location=exp.location,
                    bullets=final_bullets if final_bullets else [],  # Empty list instead of None
                    raw_text=exp.raw_text,
                )
                enhanced_experience.append(enhanced_exp)
            except Exception:
                # Fallback to original if generation fails
                enhanced_experience.append(exp)

        return enhanced_experience

    def generate_skills(
        self,
        resume: ParsedResume,
        job: JobPosting,
        max_keywords: int = 3,
        rag_context: Optional[str] = None,
    ) -> List[str]:
        """Generate enhanced skills list."""
        prompt = self.prompt_builder.build_skills_prompt(
            resume.skills, job, max_keywords, rag_context
        )

        # Language-specific system prompt for skills
        target_language = resume.language or "en"
        if target_language == "ru":
            system_prompt = (
                "Вы профессиональный писатель резюме. Оптимизируйте раздел навыков, "
                "добавляя релевантные ключевые слова, сохраняя оригинальные навыки. "
                "ВАЖНО: Пишите ПОЛНОСТЬЮ на русском языке, не смешивайте языки. "
                "Используйте русские названия технологий и навыков."
            )
        else:
            system_prompt = (
                "You are a professional resume writer. Optimize skills sections "
                "by adding relevant keywords while preserving original skills. "
                "Write COMPLETELY in English language."
            )

        try:
            # For language-specific generation, check cache but verify language
            cached_response = llm_cache.get(prompt, system_prompt)
            if cached_response:
                # Check if cached response is in the correct language
                if target_language == "ru":
                    # If Russian, verify it's actually in Russian (not English)
                    russian_chars = sum(1 for c in cached_response if '\u0400' <= c <= '\u04FF')
                    if russian_chars < len(cached_response) * 0.3:  # Less than 30% Russian chars
                        cached_response = None  # Don't use English cached response for Russian
                
                if cached_response:
                    response = cached_response
                    from app.utils.token_tracker import token_tracker
                    token_tracker.add_usage(cached=True)
            
            if not cached_response:
                response = self.llm.generate(
                    prompt, 
                    system_prompt=system_prompt, 
                    temperature=0.5,
                    max_tokens=400  # Allow enough tokens for skills list
                )
                # Cache the response
                if response:
                    llm_cache.set(prompt, response, system_prompt)

            # Parse skills from response
            skills = self._parse_skills(response)

            return skills if skills else resume.skills
        except Exception:
            return resume.skills

    def _parse_bullets(self, text: str) -> List[str]:
        """Parse bullet points from LLM response."""
        bullets = []
        lines = text.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Remove bullet markers
            line = re.sub(r"^[-•*]\s*", "", line)
            line = re.sub(r"^\d+[.)]\s*", "", line)
            line = line.strip()

            if line:
                bullets.append(line)

        return bullets

    def _parse_skills(self, text: str) -> List[str]:
        """Parse skills list from LLM response."""
        # Remove markdown code blocks if present
        text = re.sub(r"```[\w]*\n?", "", text)
        text = re.sub(r"```", "", text)

        # Split by common separators
        skills = []
        for separator in [",", "|", "\n"]:
            if separator in text:
                parts = text.split(separator)
                skills = [s.strip() for s in parts if s.strip()]
                break

        if not skills:
            # Try line by line
            skills = [line.strip() for line in text.split("\n") if line.strip()]

        return skills

