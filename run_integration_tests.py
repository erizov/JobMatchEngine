"""Script to run integration tests with files from temp/input."""

import asyncio
import sys
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.analyzers.language_detector import LanguageDetector
from app.analyzers.matcher import ResumeMatcher
from app.config import settings
from app.generators.cover_letter_generator import CoverLetterGenerator
from app.generators.resume_generator import ResumeGenerator
from app.models import JobPosting
from app.output.docx_builder import DocxBuilder
from app.output.markdown_builder import MarkdownBuilder
from app.output.text_builder import TextBuilder
from app.parsers.file_parser import FileParser
from app.parsers.job_parser import JobParser
from app.utils.cleanup import cleanup_old_files
from app.utils.hh_ru_fetcher import get_latest_hh_ru_job_url


def get_supported_extensions():
    """Get list of supported file extensions."""
    return {".docx", ".doc", ".rtf", ".txt", ".md"}


def find_resume_files(input_dir: Path):
    """
    Find all resume files in input directory.

    Args:
        input_dir: Input directory path

    Returns:
        List of file paths
    """
    if not input_dir.exists():
        return []

    supported = get_supported_extensions()
    files = []

    for file_path in input_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in supported:
            files.append(file_path)

    return sorted(files)


def create_output_filename(input_file: Path, suffix: str = "_enhanced") -> str:
    """
    Create output filename from input filename.

    Args:
        input_file: Input file path
        suffix: Suffix to add before extension

    Returns:
        Output filename
    """
    stem = input_file.stem
    ext = input_file.suffix
    return f"{stem}{suffix}{ext}"


async def process_resume_file(
    resume_file: Path,
    job: "JobPosting",
    output_dir: Path,
    file_parser: FileParser,
    job_parser: JobParser,
    language_detector: LanguageDetector,
    resume_generator: ResumeGenerator,
    cover_letter_generator: CoverLetterGenerator,
    matcher: ResumeMatcher,
    docx_builder: DocxBuilder,
    md_builder: MarkdownBuilder,
    txt_builder: TextBuilder,
    use_llm: bool = True,
    tone: str = "balanced",
):
    """
    Process a single resume file.

    Args:
        resume_file: Path to resume file
        job: Job posting to match against
        output_dir: Output directory
        file_parser: File parser instance
        job_parser: Job parser instance
        language_detector: Language detector instance
        resume_generator: Resume generator instance
        cover_letter_generator: Cover letter generator instance
        matcher: Resume matcher instance
        docx_builder: DOCX builder instance
        md_builder: Markdown builder instance
        txt_builder: Text builder instance
        use_llm: Whether to use LLM for enhancement

    Returns:
        Dictionary with processing results
    """
    print(f"\n  Processing: {resume_file.name}")
    print(f"  {'=' * 50}")

    results = {
        "file": resume_file.name,
        "status": "processing",
        "errors": [],
    }

    try:
        # Parse resume
        print(f"  [1/6] Parsing resume...")
        resume = file_parser.parse(resume_file)
        print(f"       [OK] Parsed {len(resume.raw_text)} characters")
        print(f"       [OK] Experience entries: {len(resume.experience)}")
        print(f"       [OK] Skills: {len(resume.skills)}")

        # Detect language
        print(f"  [2/6] Detecting language...")
        resume_lang = language_detector.detect_language(resume.raw_text)
        job_lang = job.language
        output_lang = language_detector.decide_output_language(
            resume_lang, job_lang, prefer_job=True
        )
        resume.language = output_lang
        print(f"       [OK] Resume language: {resume_lang}")
        print(f"       [OK] Job language: {job_lang}")
        print(f"       [OK] Output language: {output_lang}")

        # Analyze match
        print(f"  [3/6] Analyzing match...")
        match_before = matcher.analyze_match(resume, job)
        print(f"       [OK] ATS Score (before): {match_before.ats_score:.1f}/100")
        print(f"       [OK] Keyword overlap: {len(match_before.keyword_overlap)}")
        print(f"       [OK] Missing keywords: {len(match_before.missing_keywords)}")

        # Generate enhanced resume
        enhanced_resume = resume
        match_after = match_before

        if use_llm:
            print(f"  [4/6] Generating enhanced resume...")
            try:
                enhanced_resume = resume_generator.generate_enhanced_resume(
                    resume, job, tone=tone, max_keywords=3
                )
                match_after = matcher.analyze_match(enhanced_resume, job)
                improvement = match_after.ats_score - match_before.ats_score
                print(f"       [OK] Enhanced resume generated")
                print(f"       [OK] ATS Score (after): {match_after.ats_score:.1f}/100")
                print(f"       [OK] Score improvement: {improvement:+.1f}")
            except Exception as e:
                print(f"       [WARN] LLM enhancement failed: {e}")
                print(f"       [INFO] Using original resume")
                results["errors"].append(f"LLM enhancement: {str(e)}")
        else:
            print(f"  [4/6] Skipping LLM enhancement (not configured)")

        # Generate cover letter
        print(f"  [5/6] Generating cover letter...")
        try:
            cover_letter = cover_letter_generator.generate_cover_letter(
                enhanced_resume, job, tone=tone
            )
            print(f"       [OK] Cover letter generated: {len(cover_letter)} chars")
        except Exception as e:
            print(f"       [WARN] Cover letter generation failed: {e}")
            cover_letter = f"Cover letter generation failed: {str(e)}"
            results["errors"].append(f"Cover letter: {str(e)}")

        # Generate output files in both languages (RU and EN)
        print(f"  [6/6] Generating output files in 2 languages...")
        base_name = resume_file.stem

        # Generate outputs for both languages
        for lang_code in ["en", "ru"]:
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
                    phone=lang_resume.contact.phone,  # Keep original phone
                    location=lang_resume.contact.location,  # Keep original location
                    linkedin=lang_resume.contact.linkedin,
                    github=lang_resume.contact.github,
                )

            # Generate language-specific cover letter
            # Always generate in the target language to ensure proper language and contact info
            lang_cover_letter = cover_letter
            try:
                # Always regenerate cover letter for target language to ensure proper translation and contact info
                lang_cover_letter = cover_letter_generator.generate_cover_letter(
                    lang_resume, job, tone=tone
                )
            except Exception:
                # Use original if generation fails
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
                results["errors"].append(f"Resume output ({lang_code}): {str(e)}")

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
                results["errors"].append(f"Cover letter output ({lang_code}): {str(e)}")

        results["status"] = "completed"
        results["ats_score_before"] = match_before.ats_score
        results["ats_score_after"] = match_after.ats_score
        results["improvement"] = match_after.ats_score - match_before.ats_score

    except Exception as e:
        print(f"  [ERROR] Processing failed: {e}")
        results["status"] = "failed"
        results["errors"].append(str(e))

    return results


async def test_full_pipeline():
    """Test full pipeline with files from temp/input."""
    print("=" * 60)
    print("JobMatchEngine Integration Test")
    print("=" * 60)

    # Cleanup old files
    print("\n[INFO] Cleaning up old output files...")
    cleanup_result = cleanup_old_files()
    if cleanup_result["files_deleted"] > 0:
        print(
            f"  [OK] Deleted {cleanup_result['files_deleted']} old file(s) "
            f"({cleanup_result['bytes_freed'] / 1024:.1f} KB freed)"
        )
    else:
        print("  [OK] No old files to clean up")

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

    # Check LLM availability
    use_llm = False
    try:
        from app.generators.llm_client import LLMClient

        llm = LLMClient()
        use_llm = True
        print("\n[INFO] LLM client available - enhancement enabled")
    except Exception as e:
        print(f"\n[INFO] LLM not configured: {e}")
        print("[INFO] Will process files without LLM enhancement")

    # Find input files
    input_dir = settings.input_dir
    output_dir = settings.output_dir

    print(f"\n[INFO] Input directory: {input_dir}")
    print(f"[INFO] Output directory: {output_dir}")

    # Ensure directories exist
    input_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find resume files
    resume_files = find_resume_files(input_dir)

    if not resume_files:
        print(f"\n[WARN] No resume files found in {input_dir}")
        print("[INFO] Supported formats: .docx, .doc, .rtf, .txt, .md")
        print("[INFO] Please add resume files to the input directory")
        return

    print(f"\n[INFO] Found {len(resume_files)} resume file(s)")

    # Create test job posting - support both text and URL
    print("\n[INFO] Creating test job posting...")
    
    # Check for job URL in environment, or fetch latest from hh.ru
    import os
    job_url = os.getenv("TEST_JOB_URL", None) or settings.test_job_url
    
    # If no URL in env, try to fetch latest from hh.ru
    if not job_url:
        print("[INFO] No TEST_JOB_URL found, fetching latest job from hh.ru...")
        try:
            job_url = await get_latest_hh_ru_job_url()
            if job_url:
                # Clean URL (remove query parameters for cleaner URL)
                if "?" in job_url:
                    job_url = job_url.split("?")[0]
                print(f"[OK] Found latest hh.ru job: {job_url}")
                # Update environment variable for this session
                os.environ["TEST_JOB_URL"] = job_url
            else:
                print("[WARN] Could not fetch job from hh.ru")
        except Exception as e:
            print(f"[WARN] Error fetching from hh.ru: {e}")
    
    if job_url:
        print(f"[INFO] Using job URL: {job_url}")
        try:
            job = await job_parser.parse_from_url(job_url)
            if job and job.title:
                print(f"[OK] Job posting parsed from URL: {job.title}")
                if job.company:
                    print(f"[OK] Company: {job.company}")
                if job.language:
                    print(f"[OK] Language: {job.language}")
            else:
                raise ValueError("Failed to parse job posting - missing title")
        except Exception as e:
            import traceback
            print(f"[WARN] Failed to parse job from URL: {e}")
            print(f"[DEBUG] Error details: {traceback.format_exc()}")
            print("[INFO] Falling back to text-based job posting")
            job_url = None
    
    if not job_url:
        # Use text-based job posting
        job_text = """
        Position: Senior Python Developer
        Company: Tech Innovations Inc
        Location: Remote

        Requirements:
        - 5+ years of Python experience
        - Experience with FastAPI or Django
        - Knowledge of Docker and Kubernetes
        - Strong problem-solving skills
        - Experience with PostgreSQL or MongoDB

        Responsibilities:
        - Develop and maintain backend services
        - Design and implement RESTful APIs
        - Collaborate with cross-functional teams
        - Optimize system performance
        """
        job = job_parser.parse_from_text(job_text)
        print(f"[OK] Job posting created from text: {job.title}")
        if job.company:
            print(f"[OK] Company: {job.company}")

    # Process each file
    print(f"\n{'=' * 60}")
    print(f"Processing {len(resume_files)} file(s)...")
    print(f"{'=' * 60}")

    all_results = []

    for i, resume_file in enumerate(resume_files, 1):
        print(f"\n[{i}/{len(resume_files)}] {resume_file.name}")

        results = await process_resume_file(
            resume_file,
            job,
            output_dir,
            file_parser,
            job_parser,
            language_detector,
            resume_generator,
            cover_letter_generator,
            matcher,
            docx_builder,
            md_builder,
            txt_builder,
            use_llm=use_llm,
            tone="balanced",
        )

        all_results.append(results)

    # Summary
    print(f"\n{'=' * 60}")
    print("Summary")
    print(f"{'=' * 60}")

    completed = sum(1 for r in all_results if r["status"] == "completed")
    failed = sum(1 for r in all_results if r["status"] == "failed")

    print(f"\nTotal files processed: {len(all_results)}")
    print(f"  [OK] Completed: {completed}")
    print(f"  [FAIL] Failed: {failed}")

    if completed > 0:
        avg_improvement = sum(
            r.get("improvement", 0) for r in all_results if r["status"] == "completed"
        ) / completed
        print(f"\nAverage ATS score improvement: {avg_improvement:+.1f}")

    print(f"\nOutput files saved to: {output_dir}")
    print(f"\n{'=' * 60}")
    print("Integration tests completed!")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
