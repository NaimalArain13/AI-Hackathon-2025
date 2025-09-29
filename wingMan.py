import asyncio
import json
from agents import (
    Agent,
    Runner,
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
)
# ---------------- Setup ----------------
from decouple import config
set_tracing_disabled(True)

API_KEY = config("GEMINI_API_KEY")

client_provider = AsyncOpenAI(
    api_key=API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

MODEL = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client_provider,
)



wingMan = Agent(
    name="WingMan",
    model=MODEL,
    instructions="""
You are WingMan — a friendly and transparent roommate advisor. 
Your role is to help students understand their compatibility report in plain, empathetic language.  

### Core Responsibilities
1. Receive structured input with:
   - summary of conflicts
   - red flags (with severity, description, evidence, recommendations)
   - filtered out conflicts
   - overall assessment
   - mitigation strategies

2. Explain clearly:
   - Why this match works or doesn’t
   - Which red flags are most important
   - How serious the risks are
   - Why some conflicts were filtered out
   - What compromises are possible

3. Style:
   - Speak like a helpful "big sibling" or "wise motherly friend"
   - Be empathetic, practical, and culturally aware (Pakistani student context)
   - Avoid technical jargon, explain in student-friendly terms

4. Output:
   - A *transparent explanation* in natural language
   - Highlight red flags and why they matter
   - Suggest clear compromises/solutions
   - End with a *final friendly recommendation* (e.g., “You can try this match with caution”, “Better to avoid”, etc.)

### Rules
- Always explain reasoning in plain terms
- Emphasize the most critical issues first (financial, safety, lifestyle)
- Suggest compromises only if realistically possible
- Keep it balanced: don’t alarm users unnecessarily, but don’t sugarcoat either
- Final answer must be empathetic and practical
""",
)


runner = Runner()


async def run_wingman_short_advice_demo():
    # Compact structured input (mirrors RedFlagReport essentials)
    report = {
        "analysis_summary": {
            "total_conflicts_detected": 4,
            "high_confidence_flags": 4,
            "filtered_red_flags": 4,
            "overall_risk_level": "HIGH",
        },
        "red_flags": [
            {
                "flag_id": "RF001",
                "type": "significant_financial_disparity",
                "severity": "HIGH",
                "confidence": 92,
                "description": "192% budget difference (Sara: 12K vs Mariam: 35K).",
                "evidence": ["budget_disparity", "financial_stability"],
                "impact_assessment": "Unequal lifestyle and housing options",
                "recommendation": "HIGH RISK - Needs clear cost-sharing rules",
            },
            {
                "flag_id": "RF002",
                "type": "security_standard_mismatch",
                "severity": "HIGH",
                "confidence": 87,
                "description": "Female-only high security vs flexible mixed housing.",
                "evidence": ["security_preferences"],
                "impact_assessment": "Safety vs comfort tradeoff",
                "recommendation": "HIGH RISK - Safety cannot be compromised",
            },
        ],
        "filtered_out_conflicts": [],
        "overall_assessment": {
            "recommendation": "PROCEED WITH EXTREME CAUTION",
            "risk_level": "HIGH",
            "viability_score": 35,
            "reasoning": "Multiple high-confidence red flags",
        },
        "mitigation_strategies": [
            "Set cost-splitting rules",
            "Choose secure female-only housing",
            "Define quiet study hours",
        ],
    }

    prompt = (
        "Summarize this report in 4-6 short lines for students. "
        "Keep it human, empathetic, concise, and practical (under 100 words). "
        "End with a clear recommendation.\n\n"
        f"Report:\n{json.dumps(report, indent=2)}"
    )

    resp = await runner.run(
        wingMan,
        prompt,
    )

    # Print short human-readable advice
    text = getattr(resp, "output", None) or getattr(resp, "final_output", "")
    print(text if isinstance(text, str) else str(text))


if __name__ == "__main__":
    asyncio.run(run_wingman_short_advice_demo())