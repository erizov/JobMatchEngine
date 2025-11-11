"""Pydantic models for data structures."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    """Contact information from resume."""

    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None


class Experience(BaseModel):
    """Work experience entry."""

    title: str
    company: str
    dates: str
    location: Optional[str] = None
    bullets: List[str] = Field(default_factory=list)
    raw_text: str


class Education(BaseModel):
    """Education entry."""

    degree: Optional[str] = None
    institution: str
    dates: Optional[str] = None
    location: Optional[str] = None
    details: Optional[str] = None


class ParsedResume(BaseModel):
    """Structured resume data."""

    contact: ContactInfo
    summary: Optional[str] = None
    experience: List[Experience] = Field(default_factory=list)
    skills: List[str] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    languages: List[str] = Field(default_factory=list)
    language: str = Field(default="en", description="Detected language: ru or en")
    raw_text: str


class JobPosting(BaseModel):
    """Parsed job posting data."""

    title: str
    company: Optional[str] = None
    location: Optional[str] = None
    description: str
    requirements: List[str] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    must_have_keywords: List[str] = Field(default_factory=list)
    nice_to_have_keywords: List[str] = Field(default_factory=list)
    language: str = Field(default="en", description="Detected language: ru or en")
    raw_text: str


class MatchAnalysis(BaseModel):
    """Analysis of resume vs job posting match."""

    ats_score: float = Field(
        ge=0.0,
        le=100.0,
        description="ATS compatibility score (0-100)",
    )
    keyword_overlap: List[str] = Field(
        default_factory=list,
        description="Keywords present in both",
    )
    missing_keywords: List[str] = Field(
        default_factory=list,
        description="Keywords in JD but not in resume",
    )
    recommendations: List[str] = Field(
        default_factory=list,
        description="Actionable recommendations",
    )


class GenerationRequest(BaseModel):
    """Request for document generation."""

    resume_id: str
    job_id: str
    tone: str = "balanced"
    max_keywords: int = 3
    preserve_facts: bool = True


class GenerationResult(BaseModel):
    """Result of document generation."""

    job_id: str
    resume_file: str
    cover_letter_file: str
    change_summary: str
    ats_score_before: float
    ats_score_after: float
    similarity_to_original: float
    created_at: datetime = Field(default_factory=datetime.now)

