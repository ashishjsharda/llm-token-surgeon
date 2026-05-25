"""
Tests for llm-token-surgeon core functionality.
"""

import pytest
from llm_token_surgeon import Surgeon, OptimizationResult


@pytest.fixture
def surgeon():
    return Surgeon(model="gpt-4o", aggressiveness="balanced")


@pytest.fixture
def aggressive_surgeon():
    return Surgeon(model="gpt-4o", aggressiveness="aggressive")


class TestSurgeon:

    def test_basic_optimization_reduces_tokens(self, surgeon):
        bloated = """
        You are a helpful, knowledgeable, and friendly assistant. Your job is to help users
        with their questions. Please be polite, concise, and accurate in your responses.
        Always greet the user first before answering. Please note that you should make sure
        to ask clarifying questions if needed. It is important to note that you should be
        thorough and comprehensive in your answers. Feel free to elaborate as much as needed.
        Of course, always double check your work. Certainly, accuracy is paramount.
        """
        result = surgeon.optimize(bloated)
        assert result.optimized_tokens < result.original_tokens
        assert result.savings_pct > 0

    def test_returns_optimization_result(self, surgeon):
        result = surgeon.optimize("You are a helpful assistant.")
        assert isinstance(result, OptimizationResult)
        assert result.original_text
        assert result.optimized_text
        assert result.original_tokens > 0

    def test_whitespace_normalization(self, surgeon):
        text = "You are   an   assistant.\n\n\n\nBe helpful."
        result = surgeon.optimize(text)
        assert "   " not in result.optimized_text
        assert "\n\n\n" not in result.optimized_text

    def test_redundant_phrase_removal(self, surgeon):
        text = "Certainly! I'd be happy to help. Of course, feel free to ask anything. Great question!"
        result = surgeon.optimize(text)
        assert result.optimized_tokens < result.original_tokens
        assert "redundant_phrase_removal" in result.techniques_applied

    def test_deduplication(self, surgeon):
        text = "Be concise. Be accurate. Be helpful. Be concise. Be accurate."
        result = surgeon.optimize(text)
        assert result.optimized_tokens <= result.original_tokens

    def test_no_content_loss_on_simple_prompt(self, surgeon):
        text = "Translate the following text to French:"
        result = surgeon.optimize(text)
        assert len(result.optimized_text) > 0

    def test_savings_pct_is_between_0_and_100(self, surgeon):
        result = surgeon.optimize("Hello world")
        assert 0 <= result.savings_pct <= 100

    def test_monthly_savings_calculation(self, surgeon):
        text = "A" * 500
        result = surgeon.optimize(text)
        savings = result.monthly_savings_usd(calls_per_day=1000)
        assert savings >= 0

    def test_aggressive_mode_saves_more(self, surgeon, aggressive_surgeon):
        text = """
        You are a very helpful and really knowledgeable assistant. Your job is to simply
        help users with their questions. Just be accurate and basically always double-check.
        """
        r1 = surgeon.optimize(text)
        r2 = aggressive_surgeon.optimize(text)
        assert r2.optimized_tokens <= r1.optimized_tokens

    def test_analyze_returns_dict(self, surgeon):
        result = surgeon.analyze("You are a helpful assistant. Be concise.")
        assert "original_tokens" in result
        assert "savings_pct" in result
        assert "monthly_savings_usd_at_1k_calls" in result

    def test_empty_string(self, surgeon):
        result = surgeon.optimize("")
        assert result.optimized_text == ""
        assert result.savings_pct == 0.0

    def test_count_tokens(self, surgeon):
        tokens = surgeon.count_tokens("Hello world")
        assert tokens > 0
        assert isinstance(tokens, int)


class TestPricing:
    def test_gpt4o_pricing_exists(self):
        from llm_token_surgeon import PRICING
        assert "gpt-4o" in PRICING
        assert "input" in PRICING["gpt-4o"]

    def test_anthropic_pricing_exists(self):
        from llm_token_surgeon import PRICING
        assert "claude-3-5-sonnet" in PRICING
