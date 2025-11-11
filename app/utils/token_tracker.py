"""Track token usage across LLM calls."""

from typing import Dict


class TokenTracker:
    """Track token usage for LLM API calls."""

    def __init__(self):
        """Initialize token tracker."""
        self.usage: Dict[str, int] = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cached_responses": 0,  # Count of cached responses used
        }

    def add_usage(
        self,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        total_tokens: int = 0,
        cached: bool = False,
    ) -> None:
        """
        Add token usage to tracker.

        Args:
            prompt_tokens: Tokens used in prompt
            completion_tokens: Tokens used in completion
            total_tokens: Total tokens (if provided, used instead of sum)
            cached: Whether this was a cached response
        """
        if cached:
            self.usage["cached_responses"] += 1
        else:
            if total_tokens:
                self.usage["total_tokens"] += total_tokens
            else:
                self.usage["prompt_tokens"] += prompt_tokens
                self.usage["completion_tokens"] += completion_tokens
                self.usage["total_tokens"] += prompt_tokens + completion_tokens

    def get_summary(self) -> Dict[str, int]:
        """
        Get token usage summary.

        Returns:
            Dictionary with token usage statistics
        """
        return self.usage.copy()

    def reset(self) -> None:
        """Reset token usage counters."""
        self.usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "cached_responses": 0,
        }

    def __str__(self) -> str:
        """String representation of token usage."""
        cached_info = ""
        if self.usage["cached_responses"] > 0:
            cached_info = f" ({self.usage['cached_responses']} from cache)"
        return (
            f"Tokens used: {self.usage['total_tokens']} "
            f"(prompt: {self.usage['prompt_tokens']}, "
            f"completion: {self.usage['completion_tokens']}){cached_info}"
        )


# Global token tracker instance
token_tracker = TokenTracker()

