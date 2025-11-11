"""Unified LLM client interface for OpenAI, Anthropic, and Ollama."""

from typing import Dict, List, Optional, Tuple

from app.config import OPENAI_API_BASE, OPENAI_API_KEY, settings
from app.utils.token_tracker import token_tracker


class LLMClient:
    """Unified interface for different LLM providers."""

    def __init__(self):
        """Initialize LLM client based on configuration."""
        self.provider = settings.llm_provider.lower()
        self.model = settings.model_name

        if self.provider == "openai":
            self._init_openai()
        elif self.provider == "anthropic":
            self._init_anthropic()
        elif self.provider == "ollama":
            self._init_ollama()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _init_openai(self):
        """Initialize OpenAI client."""
        try:
            from openai import OpenAI

            if not OPENAI_API_KEY:
                raise ValueError("OpenAI API key not configured")
            
            # Use custom base URL if provided (for proxy endpoints)
            client_kwargs = {
                "api_key": OPENAI_API_KEY,
                "timeout": 120.0,  # 2 minute timeout for long responses
            }
            if OPENAI_API_BASE:
                client_kwargs["base_url"] = OPENAI_API_BASE
            
            self.client = OpenAI(**client_kwargs)
            self._generate = self._generate_openai
        except ImportError:
            raise ImportError("openai package not installed")

    def _init_anthropic(self):
        """Initialize Anthropic client."""
        try:
            from anthropic import Anthropic

            if not settings.anthropic_api_key:
                raise ValueError("Anthropic API key not configured")
            self.client = Anthropic(api_key=settings.anthropic_api_key)
            self._generate = self._generate_anthropic
        except ImportError:
            raise ImportError("anthropic package not installed")

    def _init_ollama(self):
        """Initialize Ollama client."""
        try:
            import ollama

            self.client = ollama
            self._generate = self._generate_ollama
        except ImportError:
            raise ImportError("ollama package not installed")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text using configured LLM.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text
        """
        content, usage = self._generate(prompt, system_prompt, temperature, max_tokens)
        # Track token usage
        if usage:
            token_tracker.add_usage(
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
            )
        return content

    def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
    ) -> Tuple[str, Optional[Dict]]:
        """Generate using OpenAI."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Ensure we get the full response content
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from LLM")
        
        # Check if response was truncated (finish_reason should be 'stop' for complete)
        finish_reason = response.choices[0].finish_reason
        if finish_reason == "length":
            # Response was truncated due to max_tokens limit
            raise ValueError(
                f"Response truncated (finish_reason: {finish_reason}). "
                f"Consider increasing max_tokens. Current content length: {len(content)}"
            )
        
        # Extract token usage
        usage = None
        if hasattr(response, "usage") and response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }
        
        return content, usage

    def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
    ) -> Tuple[str, Optional[Dict]]:
        """Generate using Anthropic."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens or 4096,
            temperature=temperature,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
        )

        # Extract token usage if available
        usage = None
        if hasattr(response, "usage"):
            usage = {
                "prompt_tokens": getattr(response.usage, "input_tokens", 0),
                "completion_tokens": getattr(response.usage, "output_tokens", 0),
                "total_tokens": (
                    getattr(response.usage, "input_tokens", 0) +
                    getattr(response.usage, "output_tokens", 0)
                ),
            }

        return response.content[0].text, usage

    def _generate_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
    ) -> Tuple[str, Optional[Dict]]:
        """Generate using Ollama."""
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        response = self.client.generate(
            model=self.model,
            prompt=full_prompt,
            options={
                "temperature": temperature,
                "num_predict": max_tokens or 2048,
            },
        )

        # Extract token usage if available
        usage = None
        if "prompt_eval_count" in response and "eval_count" in response:
            usage = {
                "prompt_tokens": response.get("prompt_eval_count", 0),
                "completion_tokens": response.get("eval_count", 0),
                "total_tokens": (
                    response.get("prompt_eval_count", 0) +
                    response.get("eval_count", 0)
                ),
            }

        return response["response"], usage

