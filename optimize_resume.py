"""Simple CLI script to optimize resume with job vacancy URL."""

import asyncio
import sys
from pathlib import Path

from app.analyzers.language_detector import LanguageDetector
from app.analyzers.matcher import ResumeMatcher
from app.config import settings
from app.generators.cover_letter_generator import CoverLetterGenerator
from app.generators.resume_generator import ResumeGenerator
from app.output.docx_builder import DocxBuilder
from app.output.markdown_builder import MarkdownBuilder
from app.output.text_builder import TextBuilder
from app.parsers.file_parser import FileParser
from app.parsers.job_parser import JobParser
from app.utils.rag_loader import load_rag_context
from typing import Optional


async def optimize_resume_cli(
    resume_path: str, 
    job_url: str, 
    tone: str = "balanced",
    output_languages: str = None,
    rag_file: Optional[str] = None,
):
    """
    Optimize resume with job vacancy URL.
    
    Args:
        resume_path: Path to resume file
        job_url: URL to job vacancy
        tone: Generation tone (conservative, balanced, aggressive)
    """
    print("=" * 60)
    print("JobMatchEngine - Resume Optimization")
    print("=" * 60)
    
    # Reset token tracker for this run
    from app.utils.token_tracker import token_tracker
    token_tracker.reset()
    
    # Initialize components
    file_parser = FileParser()
    job_parser = JobParser()
    language_detector = LanguageDetector()
    resume_generator = ResumeGenerator()
    cover_letter_generator = CoverLetterGenerator()
    matcher = ResumeMatcher()
    
    # Output builders
    docx_builder = DocxBuilder()
    md_builder = MarkdownBuilder()
    txt_builder = TextBuilder()
    
    # Parse resume
    resume_file = Path(resume_path)
    if not resume_file.exists():
        print(f"\n[ERROR] Resume file not found: {resume_path}")
        sys.exit(1)
    
    print(f"\n[1/5] Parsing resume: {resume_file.name}")
    try:
        resume = file_parser.parse(resume_file)
        print(f"       [OK] Parsed {len(resume.raw_text)} characters")
        print(f"       [OK] Experience entries: {len(resume.experience)}")
        print(f"       [OK] Skills: {len(resume.skills)}")
    except Exception as e:
        print(f"       [ERROR] Failed to parse resume: {e}")
        sys.exit(1)
    
    # Parse job posting
    print(f"\n[2/5] Parsing job posting from URL: {job_url}")
    try:
        job = await job_parser.parse_from_url(job_url)
        print(f"       [OK] Job title: {job.title}")
        if job.company:
            print(f"       [OK] Company: {job.company}")
        print(f"       [OK] Language: {job.language}")
    except Exception as e:
        print(f"       [ERROR] Failed to parse job posting: {e}")
        sys.exit(1)
    
    # Detect language and determine output languages
    print(f"\n[3/5] Detecting language...")
    resume_lang = language_detector.detect_language(resume.raw_text)
    job_lang = job.language
    
    # Use output_languages parameter or settings default
    output_langs_setting = output_languages or settings.output_languages or "ru"
    
    # Determine which languages to generate
    if output_langs_setting.lower() == "both":
        languages_to_generate = ["ru", "en"]
    elif output_langs_setting.lower() == "en":
        languages_to_generate = ["en"]
    else:  # Default to Russian only
        languages_to_generate = ["ru"]
    
    # Set primary output language for resume enhancement
    output_lang = language_detector.decide_output_language(
        resume_lang, job_lang, prefer_job=True
    )
    resume.language = output_lang
    print(f"       [OK] Resume language: {resume_lang}")
    print(f"       [OK] Job language: {job_lang}")
    print(f"       [OK] Output languages: {', '.join(languages_to_generate)}")
    
    # Analyze match
    print(f"\n[4/5] Analyzing match...")
    match_before = matcher.analyze_match(resume, job)
    print(f"       [OK] ATS Score (before): {match_before.ats_score:.1f}/100")
    print(f"       [OK] Keyword overlap: {len(match_before.keyword_overlap)}")
    print(f"       [OK] Missing keywords: {len(match_before.missing_keywords)}")
    
    # Load RAG context if provided
    rag_context = None
    if rag_file:
        print(f"\n[4.5/5] Loading RAG knowledge base from: {rag_file}")
        rag_context = load_rag_context(rag_file)
        if rag_context:
            print(f"       [OK] Loaded {len(rag_context)} characters from RAG file")
        else:
            print(f"       [WARN] Could not load RAG file, continuing without it")
    
    # Generate enhanced resume
    print(f"\n[5/5] Generating enhanced resume and cover letter...")
    try:
        enhanced_resume = resume_generator.generate_enhanced_resume(
            resume, job, tone=tone, max_keywords=3, rag_context=rag_context
        )
        match_after = matcher.analyze_match(enhanced_resume, job)
        improvement = match_after.ats_score - match_before.ats_score
        print(f"       [OK] Enhanced resume generated")
        print(f"       [OK] ATS Score (after): {match_after.ats_score:.1f}/100")
        print(f"       [OK] Score improvement: {improvement:+.1f}")
    except Exception as e:
        print(f"       [WARN] LLM enhancement failed: {e}")
        print(f"       [INFO] Using original resume")
        enhanced_resume = resume
    
    # Generate cover letter
    try:
        cover_letter = cover_letter_generator.generate_cover_letter(
            enhanced_resume, job, tone=tone
        )
        print(f"       [OK] Cover letter generated: {len(cover_letter)} chars")
    except Exception as e:
        print(f"       [WARN] Cover letter generation failed: {e}")
        cover_letter = f"Cover letter generation failed: {str(e)}"
    
    # Generate output files in both languages
    print(f"\n[6/6] Generating output files...")
    base_name = resume_file.stem
    output_dir = settings.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate outputs for selected languages
    for lang_code in languages_to_generate:
        lang_suffix = f"_{lang_code}"
        print(f"       Generating {lang_code.upper()} versions...")
        
        # Create language-specific resume copy
        lang_resume = enhanced_resume.model_copy(deep=True)
        lang_resume.language = lang_code
        
        # Set English contact info for English versions
        if lang_code == "en":
            from app.models import ContactInfo
            lang_resume.contact = ContactInfo(
                name="Eugene Rizov",
                email="erizov@yahoo.com",
                phone=lang_resume.contact.phone,
                location=lang_resume.contact.location,
                linkedin=lang_resume.contact.linkedin,
                github=lang_resume.contact.github,
            )
        
        # Generate language-specific cover letter
        lang_cover_letter = cover_letter
        try:
            lang_cover_letter = cover_letter_generator.generate_cover_letter(
                lang_resume, job, tone=tone
            )
        except Exception:
            pass
        
        # Resume outputs
        try:
            docx_builder.build_resume(
                lang_resume,
                output_dir / f"{base_name}_enhanced{lang_suffix}.docx",
            )
            print(f"         [OK] {base_name}_enhanced{lang_suffix}.docx")
            
            md_builder.build_resume(
                lang_resume, output_dir / f"{base_name}_enhanced{lang_suffix}.md"
            )
            print(f"         [OK] {base_name}_enhanced{lang_suffix}.md")
            
            txt_builder.build_resume(
                lang_resume, output_dir / f"{base_name}_enhanced{lang_suffix}.txt"
            )
            print(f"         [OK] {base_name}_enhanced{lang_suffix}.txt")
        except Exception as e:
            print(f"         [ERROR] Failed to generate {lang_code} resume: {e}")
        
        # Cover letter outputs
        try:
            docx_builder.build_cover_letter(
                lang_cover_letter,
                lang_resume.contact,
                output_dir / f"{base_name}_cover_letter{lang_suffix}.docx",
            )
            print(f"         [OK] {base_name}_cover_letter{lang_suffix}.docx")
            
            md_builder.build_cover_letter(
                lang_cover_letter,
                lang_resume.contact,
                output_dir / f"{base_name}_cover_letter{lang_suffix}.md",
            )
            print(f"         [OK] {base_name}_cover_letter{lang_suffix}.md")
            
            txt_builder.build_cover_letter(
                lang_cover_letter,
                lang_resume.contact,
                output_dir / f"{base_name}_cover_letter{lang_suffix}.txt",
            )
            print(f"         [OK] {base_name}_cover_letter{lang_suffix}.txt")
        except Exception as e:
            print(f"         [ERROR] Failed to generate {lang_code} cover letter: {e}")
    
    print(f"\n{'=' * 60}")
    print("Summary")
    print(f"{'=' * 60}")
    print(f"Resume: {resume_file.name}")
    print(f"Job: {job.title} at {job.company or 'Unknown'}")
    print(f"ATS Score: {match_before.ats_score:.1f} → {match_after.ats_score:.1f} ({improvement:+.1f})")
    print(f"\nOutput files saved to: {output_dir}")
    num_files = len(languages_to_generate) * 6  # 6 formats per language
    print(f"Generated {num_files} files (6 formats × {len(languages_to_generate)} language(s))")
    
    # Display token usage
    from app.utils.token_tracker import token_tracker
    usage = token_tracker.get_summary()
    print(f"\nToken Usage:")
    print(f"  Total tokens: {usage['total_tokens']}")
    print(f"  Prompt tokens: {usage['prompt_tokens']}")
    print(f"  Completion tokens: {usage['completion_tokens']}")
    if usage['cached_responses'] > 0:
        print(f"  Cached responses used: {usage['cached_responses']} (saved tokens)")
    
    print(f"{'=' * 60}")


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print("Usage: python optimize_resume.py <resume_file> <job_url> [tone] [output_languages] [rag_file]")
        print("\nExamples:")
        print("  python optimize_resume.py resume.docx https://hh.ru/vacancy/123456789")
        print("  python optimize_resume.py resume.docx https://hh.ru/vacancy/123456789 balanced ru")
        print("  python optimize_resume.py resume.docx https://hh.ru/vacancy/123456789 balanced both knowledge_base.txt")
        print("\nTone options: conservative, balanced (default), aggressive")
        print("Output languages: 'ru' (Russian only, default), 'en' (English only), 'both' (both languages)")
        print("RAG file: Optional path to knowledge base file for enhanced context")
        sys.exit(1)
    
    resume_path = sys.argv[1]
    job_url = sys.argv[2]
    tone = sys.argv[3] if len(sys.argv) > 3 else "balanced"
    output_languages = sys.argv[4] if len(sys.argv) > 4 else None
    rag_file = sys.argv[5] if len(sys.argv) > 5 else None
    
    asyncio.run(optimize_resume_cli(resume_path, job_url, tone, output_languages, rag_file))


if __name__ == "__main__":
    main()

