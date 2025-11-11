"""Generate cover letters."""

from app.generators.llm_client import LLMClient
from app.generators.prompt_builder import PromptBuilder
from app.models import JobPosting, ParsedResume
from app.utils.experience_calculator import get_experience_years_for_cover_letter
from app.utils.llm_cache import llm_cache
from app.utils.russian_grammar import format_years_russian, format_years_english


class CoverLetterGenerator:
    """Generate tailored cover letters."""

    def __init__(self):
        """Initialize generator."""
        self.llm = LLMClient()
        self.prompt_builder = PromptBuilder()

    def generate_cover_letter(
        self,
        resume: ParsedResume,
        job: JobPosting,
        tone: str = "balanced",
    ) -> str:
        """
        Generate cover letter for job application.

        Args:
            resume: Parsed resume
            job: Job posting
            tone: Generation tone

        Returns:
            Generated cover letter text
        """
        prompt = self.prompt_builder.build_cover_letter_prompt(
            resume, job, tone
        )

        # Determine target language
        target_language = resume.language or "en"
        
        if target_language == "ru":
            system_prompt = (
                "Вы профессиональный писатель сопроводительных писем. Пишите убедительные, "
                "персонализированные сопроводительные письма на русском языке, которые связывают "
                "профессиональный опыт кандидата с требованиями вакансии, сохраняя аутентичность. "
                "ВАЖНО: Пишите ПОЛНОСТЬЮ на русском языке, не смешивайте языки."
            )
        else:
            system_prompt = (
                "You are a professional cover letter writer. Write compelling, "
                "personalized cover letters that connect candidate backgrounds "
                "to job requirements while maintaining authenticity."
            )

        try:
            # Check cache first
            cached_response = llm_cache.get(prompt, system_prompt)
            if cached_response:
                cover_letter = cached_response
                from app.utils.token_tracker import token_tracker
                token_tracker.add_usage(cached=True)
            else:
                cover_letter = self.llm.generate(
                    prompt, 
                    system_prompt=system_prompt, 
                    temperature=0.8,
                    max_tokens=2000  # Allow enough tokens for full cover letter
                )
                # Cache the response
                if cover_letter:
                    llm_cache.set(prompt, cover_letter, system_prompt)

            # Clean up response
            cover_letter = cover_letter.strip()
            # Remove markdown formatting if present
            import re

            cover_letter = re.sub(r"^#+\s*", "", cover_letter, flags=re.MULTILINE)
            cover_letter = re.sub(r"```[\w]*\n?", "", cover_letter)
            cover_letter = re.sub(r"```", "", cover_letter)

            # Ensure actual candidate name is used (replace any "Candidate" placeholders)
            candidate_name = resume.contact.name
            if candidate_name:
                cover_letter = re.sub(
                    r"\bCandidate\b", candidate_name, cover_letter, flags=re.IGNORECASE
                )
                # Also ensure signature uses actual name
                if "Sincerely" in cover_letter or "Best regards" in cover_letter:
                    # Replace name after closing if it's still "Candidate"
                    cover_letter = re.sub(
                        r"(Sincerely|Best regards|Regards),?\s*\n\s*Candidate",
                        f"\\1,\n{candidate_name}",
                        cover_letter,
                        flags=re.IGNORECASE | re.MULTILINE,
                    )

            return cover_letter
        except Exception as e:
            # Return basic cover letter if generation fails
            return self._generate_fallback_cover_letter(resume, job)

    def _generate_fallback_cover_letter(
        self, resume: ParsedResume, job: JobPosting
    ) -> str:
        """Generate a basic fallback cover letter."""
        # Use actual candidate name from resume
        candidate_name = resume.contact.name or "Candidate"
        email = resume.contact.email or "your.email@example.com"
        
        # Use actual company name from job posting
        company_name = job.company or "the company"
        
        # Determine language
        target_language = resume.language or "en"
        
        if target_language == "ru":
            # Russian version
            if company_name and company_name != "the company":
                greeting = f"Уважаемые коллеги компании {company_name},"
            else:
                greeting = "Уважаемые коллеги,"
            
            skills_text = ", ".join(resume.skills[:5]) if resume.skills else "соответствующие навыки"
            experience_years = get_experience_years_for_cover_letter(resume, job)
            experience_years_text = format_years_russian(experience_years)
            
            cover_letter = f"""{greeting}

Я пишу, чтобы выразить свой интерес к вакансии {job.title} в компании {company_name}.

Благодаря моему опыту работы с {skills_text}, я считаю, что хорошо подхожу для этой роли. Мой опыт включает {experience_years_text} соответствующей работы.

Я заинтересован в возможности внести вклад в вашу команду и был бы рад обсудить, как мои навыки и опыт соответствуют вашим потребностям.

Спасибо за ваше внимание.

С уважением,
{candidate_name}
{email}
"""
        else:
            # English version
            if company_name and company_name != "the company":
                greeting = f"Dear Hiring Manager at {company_name},"
            else:
                greeting = "Dear Hiring Manager,"

            # Get skills for the letter
            skills_text = ", ".join(resume.skills[:5]) if resume.skills else "relevant skills"
            experience_years = get_experience_years_for_cover_letter(resume, job)
            experience_years_text = format_years_english(experience_years)

            cover_letter = f"""{greeting}

I am writing to express my interest in the {job.title} position at {company_name}.

With my background in {skills_text}, I believe I am well-suited for this role. My experience includes {experience_years_text} of relevant work experience.

I am excited about the opportunity to contribute to your team and would welcome the chance to discuss how my skills and experience align with your needs.

Thank you for your consideration.

Sincerely,
{candidate_name}
{email}
"""

        return cover_letter

