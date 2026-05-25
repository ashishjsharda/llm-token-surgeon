"""
examples/demo.py — run this to see llm-token-surgeon in action.

python examples/demo.py
"""

from llm_token_surgeon import Surgeon

surgeon = Surgeon(model="gpt-4o", aggressiveness="balanced")

prompts = {
    "bloated_system_prompt": """
        You are a helpful, knowledgeable, and friendly AI assistant. Your primary job and
        purpose is to help users with their questions and tasks. Please always be polite,
        concise, and accurate in your responses at all times. Always make sure to greet the
        user first before answering their question. Please note that it is important that
        you should ask clarifying questions if you need more information. It is important
        to note that you should be thorough and comprehensive in your answers. Feel free to
        elaborate as much as needed to give a complete answer. Of course, always double
        check your work for accuracy. Certainly, accuracy and helpfulness are paramount.
        Absolutely make sure to follow all instructions carefully.
    """,

    "verbose_user_template": """
        Hello! I hope you are doing well today. I was wondering if you could please help
        me with a question I have been thinking about. The question is really quite
        interesting and I would love to get your thoughts on it. So basically my question
        is: {user_question}. I would really appreciate your help with this. Thank you
        so very much in advance for taking the time to answer my question.
    """,

    "repetitive_instructions": """
        Always respond in JSON format. Your response must be valid JSON. Make sure your
        output is JSON. Do not include any text outside the JSON. The format should be JSON.
        Be concise. Keep responses short. Don't be verbose. Avoid long answers. Be brief.
        Be helpful. Try to be as helpful as possible. Helpfulness is important.
    """,
}

print("\n🔪 llm-token-surgeon demo\n" + "=" * 50)

total_orig = total_opt = 0

for name, prompt in prompts.items():
    result = surgeon.optimize(prompt)
    total_orig += result.original_tokens
    total_opt += result.optimized_tokens

    print(f"\n📝 {name}")
    print(f"   Before : {result.original_tokens} tokens")
    print(f"   After  : {result.optimized_tokens} tokens  (-{result.savings_pct}%)")
    print(f"   Saved  : ${result.monthly_savings_usd(50_000):,.2f}/month at 50k calls/day")
    print(f"   Applied: {', '.join(result.techniques_applied)}")
    print(f"\n   Optimized text:\n   {result.optimized_text[:200].strip()}...")

total_pct = round((1 - total_opt / total_orig) * 100, 1)
print(f"\n{'='*50}")
print(f"✅ TOTAL: {total_orig} → {total_opt} tokens  ({total_pct}% reduction)")
print(f"💰 Projected savings at 50k calls/day: see per-prompt breakdown above")
print()
