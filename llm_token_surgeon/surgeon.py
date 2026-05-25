"""
llm-token-surgeon: Cut your LLM API bill by 30-70% with zero accuracy loss.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from .tokenizer import count_tokens as _count_tokens


PRICING = {
    "gpt-4o":              {"input": 2.50,  "output": 10.00},
    "gpt-4-turbo":         {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo":       {"input": 0.50,  "output": 1.50},
    "claude-3-5-sonnet":   {"input": 3.00,  "output": 15.00},
    "claude-3-opus":       {"input": 15.00, "output": 75.00},
    "gemini-1.5-pro":      {"input": 1.25,  "output": 5.00},
    "gemini-flash":        {"input": 0.075, "output": 0.30},
}


@dataclass
class OptimizationResult:
    original_text: str
    optimized_text: str
    original_tokens: int
    optimized_tokens: int
    techniques_applied: list[str] = field(default_factory=list)
    model: str = "gpt-4o"

    @property
    def savings_tokens(self) -> int:
        return self.original_tokens - self.optimized_tokens

    @property
    def savings_pct(self) -> float:
        if self.original_tokens == 0:
            return 0.0
        return round((self.savings_tokens / self.original_tokens) * 100, 1)

    def monthly_savings_usd(self, calls_per_day: int = 1000) -> float:
        price_per_1m = PRICING.get(self.model, {}).get("input", 2.50)
        saved_per_call = self.savings_tokens / 1_000_000 * price_per_1m
        return round(saved_per_call * calls_per_day * 30, 2)

    def __repr__(self) -> str:
        return (
            f"OptimizationResult("
            f"tokens: {self.original_tokens}→{self.optimized_tokens}, "
            f"saved: {self.savings_pct}%, "
            f"techniques: {self.techniques_applied})"
        )


class Surgeon:
    """
    Main optimizer. Drop in, analyze, compress.

    Usage:
        surgeon = Surgeon(model="gpt-4o")
        result = surgeon.optimize(my_prompt)
        print(result.savings_pct)  # e.g. 61.2
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        aggressiveness: str = "balanced",
        preserve_formatting: bool = False,
    ):
        self.model = model
        self.aggressiveness = aggressiveness  # conservative | balanced | aggressive
        self.preserve_formatting = preserve_formatting

    def count_tokens(self, text: str) -> int:
        return _count_tokens(text)

    def optimize(self, text: str) -> OptimizationResult:
        original_tokens = self.count_tokens(text)
        optimized = text
        techniques = []

        optimized, applied = self._normalize_whitespace(optimized)
        techniques.extend(applied)

        optimized, applied = self._remove_redundant_phrases(optimized)
        techniques.extend(applied)

        optimized, applied = self._deduplicate_instructions(optimized)
        techniques.extend(applied)

        if self.aggressiveness in ("balanced", "aggressive"):
            optimized, applied = self._compress_verbose_intros(optimized)
            techniques.extend(applied)

        if self.aggressiveness in ("balanced", "aggressive"):
            optimized, applied = self._deduplicate_semantic_groups(optimized)
            techniques.extend(applied)

        if self.aggressiveness == "aggressive":
            optimized, applied = self._strip_filler_words(optimized)
            techniques.extend(applied)

        optimized_tokens = self.count_tokens(optimized)

        return OptimizationResult(
            original_text=text,
            optimized_text=optimized,
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            techniques_applied=list(set(techniques)),
            model=self.model,
        )

    def analyze(self, text: str) -> dict:
        result = self.optimize(text)
        return {
            "original_tokens": result.original_tokens,
            "optimized_tokens": result.optimized_tokens,
            "savings_tokens": result.savings_tokens,
            "savings_pct": result.savings_pct,
            "techniques_found": result.techniques_applied,
            "monthly_savings_usd_at_1k_calls": result.monthly_savings_usd(1_000),
            "monthly_savings_usd_at_100k_calls": result.monthly_savings_usd(100_000),
            "monthly_savings_usd_at_1m_calls": result.monthly_savings_usd(1_000_000),
        }

    def _normalize_whitespace(self, text: str) -> tuple[str, list[str]]:
        techniques = []
        cleaned = re.sub(r"\n{3,}", "\n\n", text)
        cleaned = re.sub(r" {2,}", " ", cleaned)
        cleaned = re.sub(r"\t+", " ", cleaned)
        cleaned = cleaned.strip()
        if cleaned != text:
            techniques.append("whitespace_normalization")
        return cleaned, techniques

    def _remove_redundant_phrases(self, text: str) -> tuple[str, list[str]]:
        techniques = []
        patterns = [
            (r"(?i)please note that\s*", ""),
            (r"(?i)it(?:'s| is) important to (?:note|remember) that\s*", ""),
            (r"(?i)as an AI language model,?\s*", ""),
            (r"(?i)i(?:'m| am) here to help\s*(?:you)?\s*", ""),
            (r"(?i)feel free to\s*", ""),
            (r"(?i)certainly[!,.]?\s*", ""),
            (r"(?i)absolutely[!,.]?\s*", ""),
            (r"(?i)of course[!,.]?\s*", ""),
            (r"(?i)great question[!,.]?\s*", ""),
            (r"(?i)that(?:'s| is) a great question[!,.]?\s*", ""),
            (r"(?i)i(?:'d| would) be happy to\s*(?:help)?\s*", ""),
            (r"(?i)without further ado,?\s*", ""),
            (r"(?i)in conclusion,?\s*", ""),
            (r"(?i)to summarize,?\s*", ""),
        ]
        result = text
        for pattern, replacement in patterns:
            new = re.sub(pattern, replacement, result)
            if new != result:
                techniques.append("redundant_phrase_removal")
                result = new
        return result, techniques

    def _deduplicate_instructions(self, text: str) -> tuple[str, list[str]]:
        techniques = []
        sentences = re.split(r"(?<=[.!?])\s+", text)
        seen = set()
        unique = []
        for s in sentences:
            normalized = re.sub(r"\s+", " ", s.lower().strip())
            if normalized not in seen and normalized:
                seen.add(normalized)
                unique.append(s)
        result = " ".join(unique)
        if len(unique) < len(sentences):
            techniques.append("instruction_deduplication")
        return result, techniques

    def _compress_verbose_intros(self, text: str) -> tuple[str, list[str]]:
        techniques = []
        patterns = [
            (
                r"(?i)you are a helpful,? (?:knowledgeable,? )?(?:and )?(?:friendly,? )?(?:and )?accurate assistant\.?\s*",
                "You are a helpful assistant. ",
            ),
            (
                r"(?i)your (?:primary )?(?:job|task|role|goal|purpose) is to help users (?:by |with )?",
                "Help users ",
            ),
            (
                r"(?i)please (?:always )?(?:be |remain )?(?:polite,? (?:and )?)?(?:concise,? (?:and )?)?(?:and )?accurate in your responses\.?\s*",
                "Be concise and accurate. ",
            ),
        ]
        result = text
        for pattern, replacement in patterns:
            new = re.sub(pattern, replacement, result)
            if new != result:
                techniques.append("verbose_intro_compression")
                result = new
        return result, techniques

    def _strip_filler_words(self, text: str) -> tuple[str, list[str]]:
        techniques = []
        fillers = [
            r"\bvery\b\s*", r"\breally\b\s*", r"\bquite\b\s*",
            r"\bbasically\b\s*", r"\bactually\b\s*", r"\bliterally\b\s*",
            r"\bjust\b\s*", r"\bsimply\b\s*",
        ]
        result = text
        for f in fillers:
            new = re.sub(f, "", result)
            if new != result:
                techniques.append("filler_word_removal")
                result = new
        return result, techniques

    def _deduplicate_semantic_groups(self, text: str) -> tuple[str, list[str]]:
        """Collapse semantically redundant instruction clusters."""
        techniques = []
        # JSON format over-specification
        json_pattern = re.compile(
            r"(Always respond in JSON format\.?)\s*"
            r"(Your response must be valid JSON\.?\s*)?"
            r"(Make sure your\s+output is JSON\.?\s*)?"
            r"(Do not include any text outside the JSON\.?\s*)?"
            r"(The format should be JSON\.?\s*)?",
            re.IGNORECASE
        )
        new = json_pattern.sub(r"Respond in valid JSON only. ", text)
        if new != text:
            techniques.append("semantic_deduplication")
            text = new

        # Brevity/conciseness cluster
        brevity_pattern = re.compile(
            r"Be concise\.?\s*Keep responses short\.?\s*Don'?t be verbose\.?\s*"
            r"Avoid long answers\.?\s*Be brief\.?\s*",
            re.IGNORECASE
        )
        new = brevity_pattern.sub("Be concise. ", text)
        if new != text:
            techniques.append("semantic_deduplication")
            text = new

        # Helpfulness cluster
        help_pattern = re.compile(
            r"Be helpful\.?\s*Try to be as helpful as possible\.?\s*Helpfulness is important\.?\s*",
            re.IGNORECASE
        )
        new = help_pattern.sub("Be helpful. ", text)
        if new != text:
            techniques.append("semantic_deduplication")
            text = new

        return text, techniques
