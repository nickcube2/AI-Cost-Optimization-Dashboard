#!/usr/bin/env python3
"""
Cloud-agnostic LLM client
=========================

Supports OpenAI Responses API and Anthropic Messages API.
"""

import os
from typing import Optional

import requests
from anthropic import Anthropic


class LLMClient:
    """
    Simple provider-agnostic LLM client.
    """

    def __init__(self, provider: Optional[str] = None):
        self.provider = (provider or os.getenv("LLM_PROVIDER", "openai")).lower()

        # OpenAI
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
        self.openai_base_url = os.getenv(
            "OPENAI_BASE_URL", "https://api.openai.com/v1/responses"
        )

        # Anthropic
        self.claude_key = os.getenv("CLAUDE_API_KEY")
        self.claude_model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
        self._anthropic = (
            Anthropic(api_key=self.claude_key) if self.provider == "anthropic" and self.claude_key else None
        )

    def is_configured(self) -> bool:
        if self.provider == "openai":
            return bool(self.openai_key)
        if self.provider == "anthropic":
            return bool(self.claude_key)
        if self.provider == "mock":
            return True
        return False

    def generate_text(self, prompt: str, system: Optional[str] = None, max_tokens: int = 1000) -> str:
        if self.provider == "openai":
            return self._openai_generate(prompt, system, max_tokens)
        if self.provider == "anthropic":
            return self._anthropic_generate(prompt, system, max_tokens)
        if self.provider == "mock":
            return "⚠️ LLM_PROVIDER=mock. No API call was made."
        return f"⚠️ Unknown LLM_PROVIDER: {self.provider}"

    def _openai_generate(self, prompt: str, system: Optional[str], max_tokens: int) -> str:
        if not self.openai_key:
            return "⚠️ OpenAI API key not found. Please set OPENAI_API_KEY."

        payload = {
            "model": self.openai_model,
            "input": prompt,
            "max_output_tokens": max_tokens,
        }

        if system:
            payload["instructions"] = system

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.openai_key}",
        }

        try:
            response = requests.post(self.openai_base_url, json=payload, headers=headers, timeout=60)
            if response.status_code != 200:
                return f"Error calling OpenAI API: {response.status_code} {response.text[:200]}"

            data = response.json()
            return self._extract_openai_text(data)
        except Exception as e:
            return f"Error calling OpenAI API: {str(e)}"

    def _extract_openai_text(self, data: dict) -> str:
        # Prefer SDK-only output_text if present (some proxies may include it)
        if isinstance(data, dict) and data.get("output_text"):
            return data["output_text"]

        outputs = data.get("output", []) if isinstance(data, dict) else []
        parts = []
        for item in outputs:
            if item.get("type") != "message":
                continue
            for content in item.get("content", []):
                if content.get("type") == "output_text" and "text" in content:
                    parts.append(content["text"])
                elif content.get("type") == "text" and "text" in content:
                    parts.append(content["text"])

        return "\n".join(parts).strip() if parts else "⚠️ OpenAI response contained no text output."

    def _anthropic_generate(self, prompt: str, system: Optional[str], max_tokens: int) -> str:
        if not self._anthropic:
            return "⚠️ Claude API key not found. Please set CLAUDE_API_KEY."

        try:
            # Keep compatibility with older SDK by embedding system in user prompt
            if system:
                prompt = f"{system}\n\n{prompt}"

            message = self._anthropic.messages.create(
                model=self.claude_model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )

            return message.content[0].text
        except Exception as e:
            return f"Error calling Claude API: {str(e)}"
