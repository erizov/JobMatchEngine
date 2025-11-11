"""Cleanup utilities for output directory."""

import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from app.config import settings


def cleanup_old_files(
    directory: Optional[Path] = None,
    hours: Optional[int] = None,
) -> dict:
    """
    Remove files older than specified hours from directory.

    Args:
        directory: Directory to clean (defaults to output_dir from settings)
        hours: Number of hours (defaults to OUTPUT_CLEANUP_HOURS from settings)

    Returns:
        Dictionary with cleanup statistics
    """
    if directory is None:
        directory = settings.output_dir

    if hours is None:
        hours = getattr(settings, "output_cleanup_hours", 24)

    if not directory.exists():
        return {
            "status": "skipped",
            "reason": "Directory does not exist",
            "files_deleted": 0,
            "bytes_freed": 0,
        }

    cutoff_time = datetime.now() - timedelta(hours=hours)
    files_deleted = 0
    bytes_freed = 0

    # Walk through all files in directory
    for file_path in directory.rglob("*"):
        if not file_path.is_file():
            continue

        try:
            # Get file modification time
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)

            if mtime < cutoff_time:
                file_size = file_path.stat().st_size
                file_path.unlink()
                files_deleted += 1
                bytes_freed += file_size
        except (OSError, PermissionError) as e:
            # Skip files that can't be deleted
            continue

    return {
        "status": "completed",
        "files_deleted": files_deleted,
        "bytes_freed": bytes_freed,
        "cutoff_time": cutoff_time.isoformat(),
    }

