"""Cache LLM responses to save tokens by reusing them across formats."""

import hashlib
import json
from pathlib import Path
from typing import Optional

from app.config import settings


class LLMCache:
    """Cache LLM responses to avoid redundant API calls."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize LLM cache.

        Args:
            cache_dir: Cache directory path (defaults to settings.cache_dir)
        """
        self.cache_dir = cache_dir or settings.cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate cache key from prompt and system prompt.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)

        Returns:
            Cache key (hash)
        """
        cache_data = {
            "prompt": prompt,
            "system_prompt": system_prompt or "",
        }
        cache_string = json.dumps(cache_data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(cache_string.encode("utf-8")).hexdigest()

    def get(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """
        Get cached response if available.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)

        Returns:
            Cached response or None if not found
        """
        cache_key = self._get_cache_key(prompt, system_prompt)
        cache_file = self.cache_dir / f"llm_{cache_key}.json"

        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                    return cache_data.get("response")
            except Exception:
                # If cache file is corrupted, ignore it
                return None

        return None

    def set(
        self,
        prompt: str,
        response: str,
        system_prompt: Optional[str] = None,
    ) -> None:
        """
        Cache LLM response.

        Args:
            prompt: User prompt
            response: LLM response
            system_prompt: System prompt (optional)
        """
        cache_key = self._get_cache_key(prompt, system_prompt)
        cache_file = self.cache_dir / f"llm_{cache_key}.json"

        cache_data = {
            "prompt": prompt,
            "system_prompt": system_prompt or "",
            "response": response,
        }

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception:
            # If caching fails, continue without cache
            pass

    def clear(self) -> None:
        """Clear all cached responses."""
        if self.cache_dir.exists():
            for cache_file in self.cache_dir.glob("llm_*.json"):
                try:
                    cache_file.unlink()
                except Exception:
                    pass


# Global cache instance
llm_cache = LLMCache()

