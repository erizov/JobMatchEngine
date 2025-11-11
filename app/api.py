"""FastAPI endpoints for resume optimization."""

import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

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

router = APIRouter()

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

# In-memory storage for job processing (in production, use database)
job_storage = {}


@router.post("/api/upload")
async def upload_resume(file: UploadFile = File(...)) -> dict:
    """
    Upload resume file.

    Returns:
        Dictionary with file_id and status
    """
    # Validate file type
    allowed_extensions = {".docx", ".doc", ".rtf", ".txt", ".md"}
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file_ext}. "
            f"Allowed: {', '.join(allowed_extensions)}",
        )

    # Save file
    file_id = str(uuid.uuid4())
    file_path = settings.input_dir / f"{file_id}{file_ext}"

    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return {"file_id": file_id, "status": "uploaded", "filename": file.filename}


@router.post("/api/job")
async def submit_job(
    job_url: Optional[str] = Form(None), job_text: Optional[str] = Form(None)
) -> dict:
    """
    Submit job posting (URL or text).

    Args:
        job_url: URL to job posting
        job_text: Job posting text

    Returns:
        Dictionary with job_id and status
    """
    if not job_url and not job_text:
        raise HTTPException(
            status_code=400, detail="Either job_url or job_text must be provided"
        )

    job_id = str(uuid.uuid4())

    try:
        if job_url:
            job = await job_parser.parse_from_url(job_url)
        else:
            job = job_parser.parse_from_text(job_text)

        # Store job
        job_storage[job_id] = job

        return {
            "job_id": job_id,
            "status": "parsed",
            "title": job.title,
            "company": job.company,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing job: {str(e)}")


@router.post("/api/optimize")
async def optimize_resume(
    file_id: str = Form(...),
    job_id: str = Form(...),
    tone: str = Form("balanced"),
    max_keywords: int = Form(3),
) -> dict:
    """
    Generate optimized resume and cover letter.

    Args:
        file_id: Uploaded file ID
        job_id: Job posting ID
        tone: Generation tone (conservative, balanced, aggressive)
        max_keywords: Max keywords to add per section

    Returns:
        Dictionary with result_id and status
    """
    # Find resume file
    resume_file = None
    for ext in [".docx", ".doc", ".rtf", ".txt", ".md"]:
        candidate = settings.input_dir / f"{file_id}{ext}"
        if candidate.exists():
            resume_file = candidate
            break

    if not resume_file:
        raise HTTPException(status_code=404, detail="Resume file not found")

    # Get job posting
    if job_id not in job_storage:
        raise HTTPException(status_code=404, detail="Job posting not found")

    job = job_storage[job_id]

    try:
        # Parse resume
        resume = file_parser.parse(resume_file)

        # Detect and set language
        resume_lang = language_detector.detect_language(resume.raw_text)
        job_lang = job.language
        output_lang = language_detector.decide_output_language(
            resume_lang, job_lang, prefer_job=True
        )
        resume.language = output_lang

        # Analyze match
        match_analysis = matcher.analyze_match(resume, job)

        # Generate enhanced resume
        enhanced_resume = resume_generator.generate_enhanced_resume(
            resume, job, tone=tone, max_keywords=max_keywords
        )

        # Generate cover letter
        cover_letter = cover_letter_generator.generate_cover_letter(
            enhanced_resume, job, tone=tone
        )

        # Re-analyze match with enhanced resume
        enhanced_match = matcher.analyze_match(enhanced_resume, job)

        # Generate output files
        result_id = str(uuid.uuid4())
        output_dir = settings.output_dir / result_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # Resume outputs
        docx_builder.build_resume(
            enhanced_resume, output_dir / "resume_enhanced.docx"
        )
        md_builder.build_resume(enhanced_resume, output_dir / "resume_enhanced.md")
        txt_builder.build_resume(enhanced_resume, output_dir / "resume_enhanced.txt")

        # Cover letter outputs
        docx_builder.build_cover_letter(
            cover_letter, enhanced_resume.contact, output_dir / "cover_letter.docx"
        )
        md_builder.build_cover_letter(
            cover_letter, enhanced_resume.contact, output_dir / "cover_letter.md"
        )
        txt_builder.build_cover_letter(
            cover_letter, enhanced_resume.contact, output_dir / "cover_letter.txt"
        )

        # Store result metadata
        result_data = {
            "result_id": result_id,
            "file_id": file_id,
            "job_id": job_id,
            "ats_score_before": match_analysis.ats_score,
            "ats_score_after": enhanced_match.ats_score,
            "improvement": enhanced_match.ats_score - match_analysis.ats_score,
            "recommendations": enhanced_match.recommendations,
        }
        job_storage[f"result_{result_id}"] = result_data

        return {
            "result_id": result_id,
            "status": "completed",
            "ats_score_before": match_analysis.ats_score,
            "ats_score_after": enhanced_match.ats_score,
            "improvement": enhanced_match.ats_score - match_analysis.ats_score,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error optimizing resume: {str(e)}"
        )


@router.get("/api/download/{result_id}")
async def download_result(result_id: str, file_type: str = "docx") -> FileResponse:
    """
    Download generated files.

    Args:
        result_id: Result ID
        file_type: File type (resume_docx, resume_md, resume_txt,
                  cover_letter_docx, cover_letter_md, cover_letter_txt)

    Returns:
        File response
    """
    output_dir = settings.output_dir / result_id

    file_map = {
        "resume_docx": "resume_enhanced.docx",
        "resume_md": "resume_enhanced.md",
        "resume_txt": "resume_enhanced.txt",
        "cover_letter_docx": "cover_letter.docx",
        "cover_letter_md": "cover_letter.md",
        "cover_letter_txt": "cover_letter.txt",
    }

    if file_type not in file_map:
        raise HTTPException(status_code=400, detail=f"Invalid file_type: {file_type}")

    file_path = output_dir / file_map[file_type]

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=str(file_path),
        filename=file_map[file_type],
        media_type="application/octet-stream",
    )


@router.get("/api/status/{result_id}")
async def get_status(result_id: str) -> dict:
    """Get status of optimization result."""
    result_key = f"result_{result_id}"
    if result_key not in job_storage:
        raise HTTPException(status_code=404, detail="Result not found")

    return job_storage[result_key]

