"""
SurgeonMiddleware: drop-in wrapper that auto-optimizes every LLM API call.

Usage:
    from llm_token_surgeon import SurgeonMiddleware
    import openai

    client = SurgeonMiddleware(openai.OpenAI(), aggressiveness="balanced")
    # use client exactly as before
"""

from __future__ import annotations
from typing import Any
from .surgeon import Surgeon


class SurgeonMiddleware:
    """
    Wraps an OpenAI-compatible client and auto-optimizes messages before
    each API call. Tracks cumulative savings across the session.
    """

    def __init__(self, client: Any, model: str = "gpt-4o", aggressiveness: str = "balanced"):
        self._client = client
        self._surgeon = Surgeon(model=model, aggressiveness=aggressiveness)
        self.session_tokens_saved = 0
        self.session_calls = 0
        self.chat = _ChatProxy(self)

    @property
    def session_savings_summary(self) -> dict:
        return {
            "calls": self.session_calls,
            "tokens_saved": self.session_tokens_saved,
            "avg_saved_per_call": round(self.session_tokens_saved / max(self.session_calls, 1), 1),
        }

    def _optimize_messages(self, messages: list[dict]) -> list[dict]:
        optimized = []
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str) and content:
                result = self._surgeon.optimize(content)
                self.session_tokens_saved += result.savings_tokens
                optimized.append({**msg, "content": result.optimized_text})
            else:
                optimized.append(msg)
        return optimized

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


class _ChatProxy:
    def __init__(self, middleware: SurgeonMiddleware):
        self._mw = middleware

    @property
    def completions(self):
        return _CompletionsProxy(self._mw)


class _CompletionsProxy:
    def __init__(self, middleware: SurgeonMiddleware):
        self._mw = middleware

    def create(self, messages: list[dict], **kwargs) -> Any:
        optimized = self._mw._optimize_messages(messages)
        self._mw.session_calls += 1
        return self._mw._client.chat.completions.create(messages=optimized, **kwargs)
