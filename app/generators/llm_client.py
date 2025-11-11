"""Unified LLM client interface for OpenAI, Anthropic, and Ollama."""

from typing import List, Optional

from app.config import settings


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

            if not settings.openai_api_key:
                raise ValueError("OpenAI API key not configured")
            self.client = OpenAI(api_key=settings.openai_api_key)
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
        return self._generate(prompt, system_prompt, temperature, max_tokens)

    def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
    ) -> str:
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

        return response.choices[0].message.content

    def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
    ) -> str:
        """Generate using Anthropic."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens or 4096,
            temperature=temperature,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
        )

        return response.content[0].text

    def _generate_ollama(
        self,
        prompt: str,
        system_prompt: Optional[str],
        temperature: float,
        max_tokens: Optional[int],
    ) -> str:
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

        return response["response"]

