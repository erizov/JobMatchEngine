"""Fetch latest job postings from hh.ru."""

import asyncio
from typing import Optional

import httpx
from bs4 import BeautifulSoup


async def fetch_latest_hh_ru_job(
    keywords: list[str] = None, max_pages: int = 2
) -> Optional[str]:
    """
    Fetch the latest job posting URL from hh.ru matching keywords.

    Args:
        keywords: List of keywords to search for (default: ["AI", "Java", "ML"])
        max_pages: Maximum number of search result pages to check

    Returns:
        URL of the latest matching job posting, or None if not found
    """
    if keywords is None:
        keywords = ["AI", "Java", "ML"]

    # Build search query - use OR logic
    query = " OR ".join(keywords)
    base_url = "https://hh.ru/search/vacancy"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        for page in range(max_pages):
            try:
                # Search for vacancies
                params = {
                    "text": query,
                    "page": page,
                    "order_by": "publication_time",  # Sort by newest first
                }

                response = await client.get(
                    base_url, params=params, timeout=30.0
                )
                response.raise_for_status()

                # Handle encoding
                try:
                    html = response.text
                except UnicodeDecodeError:
                    html = response.content.decode("utf-8", errors="ignore")

                soup = BeautifulSoup(html, "lxml")

                # Find job posting links - try multiple selectors
                job_links = []
                
                # Method 1: data-qa attribute
                job_links.extend(
                    soup.find_all("a", {"data-qa": "serp-item__title", "href": True})
                )
                
                # Method 2: class-based selector
                if not job_links:
                    job_links.extend(
                        soup.find_all("a", class_=lambda x: x and "serp-item__title" in str(x), href=True)
                    )
                
                # Method 3: href pattern
                if not job_links:
                    job_links.extend(
                        soup.find_all("a", href=lambda x: x and "/vacancy/" in str(x))
                    )

                for link in job_links[:5]:  # Check first 5 links
                    href = link.get("href", "")
                    if not href:
                        continue

                    # Make full URL if relative
                    if href.startswith("/"):
                        href = f"https://hh.ru{href}"

                    # Clean URL (remove query parameters)
                    if "?" in href:
                        href = href.split("?")[0]

                    # Check if URL contains vacancy ID
                    if "/vacancy/" in href and href.count("/vacancy/") == 1:
                        # Verify it's a valid vacancy URL (has numeric ID)
                        vacancy_id = href.split("/vacancy/")[-1].split("?")[0]
                        if vacancy_id.isdigit():
                            return href

            except Exception as e:
                # Continue to next page if this one fails
                continue

    return None


async def get_latest_hh_ru_job_url() -> Optional[str]:
    """
    Get the latest hh.ru job URL matching AI/Java/ML.

    Returns:
        Job posting URL or None
    """
    return await fetch_latest_hh_ru_job(keywords=["AI", "Java", "ML"])

