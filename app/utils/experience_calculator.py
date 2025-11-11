"""Utilities for calculating experience years from resume and job postings."""

import re
from datetime import datetime
from typing import List, Optional

from app.models import Experience, JobPosting, ParsedResume


def calculate_years_from_experience(experiences: List[Experience]) -> float:
    """
    Calculate total years of experience from experience entries.
    
    Args:
        experiences: List of Experience objects
        
    Returns:
        Total years of experience (as float)
    """
    if not experiences:
        return 0.0
    
    total_months = 0
    current_date = datetime.now()
    
    for exp in experiences:
        if not exp.dates:
            continue
            
        # Parse dates - support various formats
        # Examples: "2020 - Present", "2020-2023", "Jan 2020 - Dec 2022", "01/2020 - 12/2022"
        dates_str = exp.dates.strip()
        
        # Check for "Present" or "Current"
        is_present = bool(re.search(r"(?i)(present|current|now|по настоящее время|текущий)", dates_str))
        
        # Extract years - find all 4-digit years (simpler and more reliable)
        year_pattern = r"\b(19\d{2}|20\d{2})\b"
        year_matches = re.findall(year_pattern, dates_str)
        years = [int(y) for y in year_matches]
        
        if not years:
            # Try month-year format
            month_year_pattern = r"(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})"
            month_years = re.findall(month_year_pattern, dates_str, re.IGNORECASE)
            if month_years:
                years = [int(my[1]) for my in month_years]
        
        if len(years) >= 2:
            # Two dates found
            start_year = int(years[0])
            end_year = int(years[1])
            months = (end_year - start_year) * 12
            total_months += months
        elif len(years) == 1 and is_present:
            # One date + Present
            start_year = int(years[0])
            end_year = current_date.year
            end_month = current_date.month
            start_month = 1  # Default to January if not specified
            
            # Try to extract start month
            month_names = {
                "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
            }
            for month_name, month_num in month_names.items():
                if re.search(month_name, dates_str, re.IGNORECASE):
                    start_month = month_num
                    break
            
            months = (end_year - start_year) * 12 + (end_month - start_month)
            total_months += months
        elif len(years) == 1:
            # Single year - assume 1 year
            total_months += 12
    
    # Convert months to years (with decimal precision)
    years = total_months / 12.0
    return round(years, 1)


def extract_required_years_from_job(job: JobPosting) -> Optional[float]:
    """
    Extract required years of experience from job posting.
    
    Args:
        job: JobPosting object
        
    Returns:
        Required years (as float) or None if not found
    """
    # Search in description and requirements
    text_to_search = f"{job.description} {' '.join(job.requirements)}"
    
    # Patterns for years: "3-5 years", "3+ years", "3 years", "3-5 лет", "от 3 до 5 лет"
    patterns = [
        r"(?:от|from|min|minimum)\s*(\d+)\s*(?:до|to|max|maximum|-)\s*(\d+)\s*(?:years?|лет|года|годов)",  # от 3 до 5 лет
        r"(\d+)\s*[-–—]\s*(\d+)\s*(?:years?|лет|года|годов)",  # 3-5 years
        r"(\d+)\s*\+\s*(?:years?|лет|года|годов)",  # 3+ years
        r"(?:от|from|min|minimum)\s*(\d+)\s*(?:years?|лет|года|годов)",  # от 3 лет
        r"(\d+)\s*(?:years?|лет|года|годов)\s*(?:of|опыта|experience)",  # 3 years of experience
        r"(\d+)\s*(?:years?|лет|года|годов)",  # 3 years
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text_to_search, re.IGNORECASE)
        if matches:
            # Handle range (e.g., "3-5")
            if isinstance(matches[0], tuple) and len(matches[0]) == 2:
                min_years = int(matches[0][0])
                max_years = int(matches[0][1])
                # Return medium value
                return (min_years + max_years) / 2.0
            elif isinstance(matches[0], tuple) and len(matches[0]) == 1:
                return float(matches[0][0])
            elif isinstance(matches[0], str):
                return float(matches[0])
    
    return None


def get_experience_years_for_cover_letter(resume: ParsedResume, job: JobPosting) -> float:
    """
    Get appropriate years of experience to use in cover letter.
    
    Priority:
    1. Calculate from actual resume experience
    2. Use required years from job posting (medium value if range)
    3. Fallback to count of experience entries
    
    Args:
        resume: ParsedResume object
        job: JobPosting object
        
    Returns:
        Years of experience (as float)
    """
    # First, try to calculate from actual dates
    calculated_years = calculate_years_from_experience(resume.experience)
    
    if calculated_years > 0:
        return calculated_years
    
    # Second, try to get required years from job posting
    required_years = extract_required_years_from_job(job)
    if required_years and required_years > 0:
        return required_years
    
    # Third, use count of experience entries if > 0
    entry_count = len(resume.experience)
    if entry_count > 0:
        return float(entry_count)
    
    # Final fallback: use 3 years as reasonable default
    # This prevents showing "0 years" which looks unprofessional
    return 3.0

