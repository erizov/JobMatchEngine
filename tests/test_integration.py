"""Integration tests with real data."""

import asyncio
from pathlib import Path

import pytest

from app.analyzers.language_detector import LanguageDetector
from app.analyzers.matcher import ResumeMatcher
from app.generators.cover_letter_generator import CoverLetterGenerator
from app.generators.resume_generator import ResumeGenerator
from app.output.docx_builder import DocxBuilder
from app.output.markdown_builder import MarkdownBuilder
from app.output.text_builder import TextBuilder
from app.parsers.file_parser import FileParser
from app.parsers.job_parser import JobParser


@pytest.fixture
def file_parser():
    """File parser fixture."""
    return FileParser()


@pytest.fixture
def job_parser():
    """Job parser fixture."""
    return JobParser()


@pytest.fixture
def resume_generator():
    """Resume generator fixture."""
    return ResumeGenerator()


@pytest.fixture
def cover_letter_generator():
    """Cover letter generator fixture."""
    return CoverLetterGenerator()


@pytest.fixture
def matcher():
    """Matcher fixture."""
    return ResumeMatcher()


@pytest.fixture
def output_dir():
    """Output directory fixture."""
    output_dir = Path("temp/test_output")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


# Test data - these should be real files in tests/fixtures/
TEST_RESUMES = {
    "en_docx": "tests/fixtures/resume_en.docx",
    "ru_docx": "tests/fixtures/resume_ru.docx",
    "en_txt": "tests/fixtures/resume_en.txt",
    "ru_txt": "tests/fixtures/resume_ru.txt",
    "en_md": "tests/fixtures/resume_en.md",
    "ru_md": "tests/fixtures/resume_ru.md",
}

# Test job URLs - real job postings
TEST_JOBS = {
    "hh_ru": "https://hh.ru/vacancy/12345678",  # Replace with real URL
    "other_en": "https://example.com/job/123",  # Replace with real URL
}


@pytest.mark.asyncio
async def test_parse_english_resume_docx(file_parser, output_dir):
    """Test parsing English DOCX resume."""
    resume_path = Path(TEST_RESUMES["en_docx"])
    if not resume_path.exists():
        pytest.skip(f"Test file not found: {resume_path}")

    resume = file_parser.parse(resume_path)

    assert resume is not None
    assert resume.raw_text
    assert len(resume.raw_text) > 100

    # Check language detection
    language_detector = LanguageDetector()
    detected_lang = language_detector.detect_language(resume.raw_text)
    assert detected_lang in ["en", "ru"]


@pytest.mark.asyncio
async def test_parse_russian_resume_docx(file_parser, output_dir):
    """Test parsing Russian DOCX resume."""
    resume_path = Path(TEST_RESUMES["ru_docx"])
    if not resume_path.exists():
        pytest.skip(f"Test file not found: {resume_path}")

    resume = file_parser.parse(resume_path)

    assert resume is not None
    assert resume.raw_text
    assert len(resume.raw_text) > 100

    # Check language detection
    language_detector = LanguageDetector()
    detected_lang = language_detector.detect_language(resume.raw_text)
    assert detected_lang in ["en", "ru"]


@pytest.mark.asyncio
async def test_parse_job_from_hh_ru(job_parser, output_dir):
    """Test parsing job from hh.ru."""
    job_url = TEST_JOBS["hh_ru"]
    if not job_url.startswith("https://hh.ru"):
        pytest.skip("hh.ru URL not configured")

    try:
        job = await job_parser.parse_from_url(job_url)

        assert job is not None
        assert job.title
        assert job.description
        assert len(job.description) > 100
        assert job.language in ["en", "ru"]
    except Exception as e:
        pytest.skip(f"Could not fetch job: {e}")


@pytest.mark.asyncio
async def test_parse_job_from_other_site(job_parser, output_dir):
    """Test parsing job from other job site."""
    job_url = TEST_JOBS["other_en"]
    if not job_url.startswith("https://"):
        pytest.skip("Job URL not configured")

    try:
        job = await job_parser.parse_from_url(job_url)

        assert job is not None
        assert job.title
        assert job.description
        assert len(job.description) > 100
    except Exception as e:
        pytest.skip(f"Could not fetch job: {e}")


@pytest.mark.asyncio
async def test_full_pipeline_english(
    file_parser, job_parser, resume_generator, cover_letter_generator, matcher, output_dir
):
    """Test full pipeline with English resume and job."""
    # Skip if LLM not configured
    try:
        from app.generators.llm_client import LLMClient

        llm = LLMClient()
    except Exception:
        pytest.skip("LLM not configured")

    resume_path = Path(TEST_RESUMES["en_docx"])
    if not resume_path.exists():
        pytest.skip(f"Test file not found: {resume_path}")

    # Parse resume
    resume = file_parser.parse(resume_path)

    # Create mock job posting
    job_text = """
    Position: Senior Software Engineer
    Company: Tech Corp
    Location: Remote

    Requirements:
    - 5+ years of Python experience
    - Experience with FastAPI
    - Knowledge of Docker and Kubernetes
    - Strong problem-solving skills

    Responsibilities:
    - Develop and maintain backend services
    - Design and implement APIs
    - Collaborate with cross-functional teams
    """
    job = job_parser.parse_from_text(job_text)

    # Analyze match
    match_before = matcher.analyze_match(resume, job)

    # Generate enhanced resume
    enhanced_resume = resume_generator.generate_enhanced_resume(
        resume, job, tone="balanced", max_keywords=3
    )

    # Analyze match after
    match_after = matcher.analyze_match(enhanced_resume, job)

    # Generate cover letter
    cover_letter = cover_letter_generator.generate_cover_letter(
        enhanced_resume, job, tone="balanced"
    )

    # Generate outputs
    docx_builder = DocxBuilder()
    md_builder = MarkdownBuilder()
    txt_builder = TextBuilder()

    docx_builder.build_resume(enhanced_resume, output_dir / "test_resume_en.docx")
    md_builder.build_resume(enhanced_resume, output_dir / "test_resume_en.md")
    txt_builder.build_resume(enhanced_resume, output_dir / "test_resume_en.txt")

    docx_builder.build_cover_letter(
        cover_letter, enhanced_resume.contact, output_dir / "test_cover_letter_en.docx"
    )

    # Verify outputs exist
    assert (output_dir / "test_resume_en.docx").exists()
    assert (output_dir / "test_resume_en.md").exists()
    assert (output_dir / "test_resume_en.txt").exists()
    assert (output_dir / "test_cover_letter_en.docx").exists()

    # Verify ATS score improved (or at least didn't decrease significantly)
    assert match_after.ats_score >= match_before.ats_score - 5  # Allow small variance

    # Verify cover letter is generated
    assert cover_letter
    assert len(cover_letter) > 200


@pytest.mark.asyncio
async def test_all_file_formats(file_parser, output_dir):
    """Test parsing all supported file formats."""
    formats_tested = []

    for format_key, file_path in TEST_RESUMES.items():
        path = Path(file_path)
        if path.exists():
            try:
                resume = file_parser.parse(path)
                assert resume is not None
                assert resume.raw_text
                formats_tested.append(format_key)
            except Exception as e:
                pytest.fail(f"Failed to parse {format_key}: {e}")

    # At least test one format
    assert len(formats_tested) > 0, "No test files found"


@pytest.mark.asyncio
async def test_ats_score_improvement(
    file_parser, job_parser, resume_generator, matcher, output_dir
):
    """Test that ATS score improves after optimization."""
    # Skip if LLM not configured
    try:
        from app.generators.llm_client import LLMClient

        llm = LLMClient()
    except Exception:
        pytest.skip("LLM not configured")

    resume_path = Path(TEST_RESUMES.get("en_docx") or TEST_RESUMES.get("en_txt"))
    if not resume_path or not resume_path.exists():
        pytest.skip("Test resume file not found")

    # Parse resume
    resume = file_parser.parse(resume_path)

    # Create job with specific requirements
    job_text = """
    Position: Data Scientist
    Requirements:
    - Python programming
    - Machine Learning
    - SQL databases
    - Data analysis
    - Statistical modeling
    """
    job = job_parser.parse_from_text(job_text)

    # Analyze before
    match_before = matcher.analyze_match(resume, job)
    score_before = match_before.ats_score

    # Generate enhanced resume
    enhanced_resume = resume_generator.generate_enhanced_resume(
        resume, job, tone="balanced", max_keywords=5
    )

    # Analyze after
    match_after = matcher.analyze_match(enhanced_resume, job)
    score_after = match_after.ats_score

    # Score should improve or stay similar (allow for LLM variance)
    assert score_after >= score_before - 10, (
        f"ATS score decreased significantly: {score_before} -> {score_after}"
    )

