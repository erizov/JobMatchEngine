"""Build prompts for LLM generation with constraints."""

from typing import List, Optional

from app.models import Experience, JobPosting, ParsedResume


class PromptBuilder:
    """Build prompts for resume and cover letter generation."""

    def build_resume_summary_prompt(
        self,
        original_summary: Optional[str],
        resume: ParsedResume,
        job: JobPosting,
        tone: str = "balanced",
    ) -> str:
        """
        Build prompt for generating optimized resume summary.

        Args:
            original_summary: Original summary text
            job: Job posting
            tone: Generation tone (conservative, balanced, aggressive)

        Returns:
            Prompt string
        """
        tone_instruction = self._get_tone_instruction(tone)
        
        # Determine target language
        target_language = resume.language or "en"
        language_instruction = ""
        if target_language == "ru":
            language_instruction = "\nCRITICAL: Write the ENTIRE summary in Russian language. Use Russian grammar and vocabulary. Do not mix English and Russian."
        else:
            language_instruction = "\nWrite the summary in English language."

        prompt = f"""You are a professional resume optimizer. Generate an optimized professional summary for a resume.

Job Title: {job.title}
Job Requirements: {', '.join(job.must_have_keywords[:10])}

{tone_instruction}
{language_instruction}

Original Summary:
{original_summary if original_summary else 'None provided'}

Candidate Background:
- Experience: {len(resume.experience)} positions
- Key Skills: {', '.join(resume.skills[:10])}

Instructions:
1. Create a 3-4 sentence professional summary (50-80 words)
2. Highlight relevant experience and skills that match the job
3. Include key keywords from job requirements naturally
4. Maintain professional tone
5. DO NOT invent facts, companies, or experiences not in the original
6. Preserve the candidate's actual background
7. Write COMPLETELY in {target_language.upper()} language

Generate the optimized summary:"""

        return prompt

    def build_experience_bullet_prompt(
        self,
        experience: Experience,
        job: JobPosting,
        tone: str = "balanced",
    ) -> str:
        """
        Build prompt for optimizing experience bullets.

        Args:
            experience: Experience entry
            job: Job posting
            tone: Generation tone

        Returns:
            Prompt string
        """
        tone_instruction = self._get_tone_instruction(tone)
        
        # Note: Language is determined from resume context, but we'll add instruction if needed
        # For now, keep technical terms in original language but allow translation

        bullets_text = "\n".join([f"- {b}" for b in experience.bullets])

        prompt = f"""Optimize work experience bullets for ATS compatibility while preserving facts.

Job Title: {job.title}
Relevant Keywords: {', '.join(job.must_have_keywords[:8])}

{tone_instruction}

Original Experience:
Title: {experience.title}
Company: {experience.company}
Dates: {experience.dates}
Bullets:
{bullets_text}

Instructions:
1. Rewrite each bullet to be achievement-focused (use action verbs)
2. Include relevant keywords from job requirements where applicable
3. Add quantifiable metrics if mentioned in original (DO NOT invent numbers)
4. Keep each bullet to 10-16 words
5. Maintain all factual information (company, dates, role)
6. Use strong action verbs (developed, implemented, led, etc.)

Generate optimized bullets (one per line, with - prefix):"""

        return prompt

    def build_skills_prompt(
        self,
        original_skills: List[str],
        job: JobPosting,
        max_additions: int = 3,
    ) -> str:
        """
        Build prompt for optimizing skills section.

        Args:
            original_skills: Original skills list
            job: Job posting
            max_additions: Maximum new skills to add

        Returns:
            Prompt string
        """
        prompt = f"""Optimize skills section for job application.

Job Title: {job.title}
Required Skills: {', '.join(job.must_have_keywords[:15])}

Original Skills:
{', '.join(original_skills)}

Instructions:
1. Keep all original skills
2. Add up to {max_additions} relevant skills from job requirements that are related to original skills
3. DO NOT add completely unrelated skills
4. Format as comma-separated list
5. Group related skills together

Generate optimized skills list:"""

        return prompt

    def build_cover_letter_prompt(
        self,
        resume: ParsedResume,
        job: JobPosting,
        tone: str = "balanced",
    ) -> str:
        """
        Build prompt for generating cover letter.

        Args:
            resume: Parsed resume
            job: Job posting
            tone: Generation tone

        Returns:
            Prompt string
        """
        tone_instruction = self._get_tone_instruction(tone)

        # Summarize experience
        exp_summary = []
        for exp in resume.experience[:3]:  # Top 3 experiences
            exp_summary.append(f"{exp.title} at {exp.company}")

        # Get candidate name
        candidate_name = resume.contact.name or "Candidate"
        
        # Get company name - use actual company from job posting
        company_name = job.company or "the company"
        
        # Determine greeting - use company name if available, otherwise generic
        greeting = f"Dear Hiring Manager at {company_name}" if company_name != "the company" else "Dear Hiring Manager"

        # Determine target language from resume
        target_language = resume.language or "en"
        language_instruction = ""
        if target_language == "ru":
            language_instruction = "\nCRITICAL: Write the ENTIRE cover letter in Russian language. Use Russian grammar, vocabulary, and professional phrases. Do not mix English and Russian - write completely in Russian."
            greeting_ru = f"Уважаемые коллеги" if company_name == "the company" else f"Уважаемые коллеги компании {company_name}"
            closing_ru = "С уважением"
        else:
            language_instruction = "\nWrite the cover letter in English language."
            greeting_ru = greeting
            closing_ru = "Sincerely"

        prompt = f"""Write a professional cover letter for a job application.

Job Title: {job.title}
Company: {company_name}
Job Requirements: {', '.join(job.must_have_keywords[:10])}

Candidate Background:
- Name: {candidate_name}
- Experience: {', '.join(exp_summary)}
- Key Skills: {', '.join(resume.skills[:10])}
- Summary: {resume.summary or 'Experienced professional'}

{tone_instruction}
{language_instruction}

Instructions:
1. Write 3-4 paragraphs (200-300 words total)
2. Start with: "{greeting_ru if target_language == 'ru' else greeting},"
3. First paragraph: Express interest in the {job.title} position at {company_name}
4. Second paragraph: Highlight relevant experience and skills
5. Third paragraph: Connect candidate's background to job requirements
6. Closing paragraph: Express enthusiasm and request interview
7. End with: "{closing_ru},\n{candidate_name}"
8. Use professional, confident tone
9. DO NOT invent facts, companies, or experiences
10. Only use information from the candidate's actual background
11. Use the actual company name "{company_name}" throughout, not placeholders
12. Write COMPLETELY in {target_language.upper()} language - do not mix languages

Generate the cover letter:"""

        return prompt

    def _get_tone_instruction(self, tone: str) -> str:
        """Get instruction based on tone."""
        tone = tone.lower()
        if tone == "conservative":
            return (
                "Tone: Conservative - Make minimal changes, preserve original "
                "wording as much as possible, only add essential keywords."
            )
        elif tone == "aggressive":
            return (
                "Tone: Aggressive - Optimize heavily for ATS, rephrase for "
                "maximum keyword density while maintaining readability."
            )
        else:  # balanced
            return (
                "Tone: Balanced - Optimize for ATS while preserving original "
                "voice and style. Add keywords naturally, improve clarity."
            )

