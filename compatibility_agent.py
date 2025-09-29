import os
import json
import asyncio
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, ValidationError
from agents import (
    Agent,
    Runner,
    AgentOutputSchema,
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

Model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=client_provider,
)


# ---------------- Schema ----------------
class ProfileSchema(BaseModel):
    id: str
    city: Optional[str] = None
    area: Optional[str] = None
    budget_PKR: Optional[int] = None
    sleep_schedule: Optional[str] = None
    cleanliness: Optional[str] = None
    noise_tolerance: Optional[str] = None
    study_habits: Optional[str] = None
    food_pref: Optional[str] = None
    security_requirement: Optional[str] = None
    location_priority: Optional[str] = None


class OutputProfileSchema(BaseModel):
    name: str = Field(default="Unknown")  # Derive name from id or default
    budget: Optional[int] = None
    lifestyle: Optional[str] = None
    guests_policy: Optional[str] = None
    substance_use: Optional[str] = None


class DetectedConflict(BaseModel):
    type: str
    severity: str
    confidence: int


class CompatibilityAnalysis(BaseModel):
    compatibility_score: int = Field(ge=0, le=100)
    profile_a: OutputProfileSchema
    profile_b: OutputProfileSchema
    detected_conflicts: List[DetectedConflict] = []


# ---------------- Agent ----------------
compatibility_scorer = Agent(
    name="CompatibilityScorer",
    model=Model,
    instructions="""
    You are a CompatibilityScorer Agent that compares two student profiles and assigns a compatibility score (0–100) based on attributes derived from the input data. Map the input fields (id, city, area, budget_PKR, sleep_schedule, cleanliness, noise_tolerance, study_habits, food_pref, security_requirement, location_priority) to output fields (name, budget, lifestyle, guests_policy, substance_use). Calculate the compatibility score using rule-based logic and identify conflicts with their severity and confidence levels.

    Input: Two JSON objects representing student profiles (student_a and student_b) with fields: id, city, area, budget_PKR, sleep_schedule, cleanliness, noise_tolerance, study_habits, food_pref, security_requirement, location_priority.
    Output: A JSON object with:
    - compatibility_score: A score (0–100) reflecting overall compatibility.
    - profile_a: Object with fields {name (derived from id or default 'Unknown'), budget (from budget_PKR), lifestyle (inferred from sleep_schedule and noise_tolerance), guests_policy (inferred from security_requirement), substance_use (inferred as 'not_applicable' if no data)}.
    - profile_b: Same structure as profile_a for the second profile.
    - detected_conflicts: List of objects with {type, severity (e.g., 'low', 'high', 'critical'), confidence (0–100)} for each mismatch.

    Mapping Rules:
    - name: Use id as a proxy (e.g., "R-387" becomes "Student R-387") or default to 'Unknown'.
    - budget: Directly use budget_PKR.
    - lifestyle: Infer from sleep_schedule (e.g., 'flexible' or 'night_owl' suggests 'relaxed', 'early' suggests 'structured') and noise_tolerance (e.g., 'high' suggests 'social', 'low' suggests 'quiet').
    - guests_policy: Infer from security_requirement (e.g., 'female_only_high_security' suggests 'no_overnight_guests', 'flexible_mixed_housing_ok' suggests 'open_to_guests').
    - substance_use: Default to 'not_applicable' unless evidence suggests otherwise.

    Scoring Logic:
    - Start with a base score of 100.
    - Deduct points for mismatches:
      - Budget: Up to 20 points for differences > 50% (e.g., abs(budget_a - budget_b) / max(budget_a, budget_b) * 100).
      - Lifestyle: Up to 30 points if lifestyles differ significantly (e.g., 'relaxed' vs 'structured').
      - Guests Policy: Up to 25 points if policies conflict (e.g., 'no_overnight_guests' vs 'open_to_guests').
      - Any other significant mismatch: Up to 25 points.
    - Cap total deductions at 100, so compatibility_score = 100 - total_deductions.
    - Identify conflicts with:
      - Type: 'lifestyle_mismatch', 'guest_policy', 'budget_disparity', or 'other_mismatch'.
      - Severity: 'low' (0–33% deduction), 'high' (34–66% deduction), 'critical' (67–100% deduction).
      - Confidence: 60–95 based on the magnitude of the mismatch.

    Example Profiles:
    student_a: {id: "R-387", budget_PKR: 24000, sleep_schedule: "flexible", cleanliness: "medium", noise_tolerance: "medium", study_habits: "Prefers studying in a library setting", food_pref: "Flexible"}
    student_b: {id: "R-388", budget_PKR: 30000, sleep_schedule: "night_owl", cleanliness: "low", noise_tolerance: "high", study_habits: "Online classes", food_pref: "Non-veg"}

    Example Output:
    {
      "compatibility_score": 65,
      "profile_a": {"name": "Student R-387", "budget": 24000, "lifestyle": "relaxed", "guests_policy": "no_overnight_guests", "substance_use": "not_applicable"},
      "profile_b": {"name": "Student R-388", "budget": 30000, "lifestyle": "social", "guests_policy": "open_to_guests", "substance_use": "not_applicable"},
      "detected_conflicts": [
        {"type": "lifestyle_mismatch", "severity": "high", "confidence": 85},
        {"type": "guest_policy", "severity": "high", "confidence": 80}
      ]
    }

    Ensure the output is structured, valid JSON with all fields present and numerical values within specified ranges.
    """,
    output_type=AgentOutputSchema(CompatibilityAnalysis, strict_json_schema=False),
)

runner = Runner()


# ---------------- Main Function ----------------
async def score_compatibility(profile_a: dict, profile_b: dict) -> dict:
    message = f"""
    Compare these two student profiles and assess their compatibility:
    student_a: {json.dumps(profile_a)}
    student_b: {json.dumps(profile_b)}
    """
    try:
        resp = await runner.run(
            compatibility_scorer,
            message,
        )
        result = {}
        if hasattr(resp, "output"):
            result = resp.output.model_dump()
        elif hasattr(resp, "final_output"):
            result = resp.final_output.model_dump()
        result["profile_a_id"] = profile_a.get("id", "unknown")
        result["profile_b_id"] = profile_b.get("id", "unknown")
    except ValidationError as e:
        print(f"Validation error: {e}. Using fallback calculation.")
        result = {
            "profile_a_id": profile_a.get("id", "unknown"),
            "profile_b_id": profile_b.get("id", "unknown"),
            "profile_a": OutputProfileSchema(
                name=f"Student {profile_a.get('id', 'Unknown')}",
                budget=profile_a.get("budget_PKR"),
                lifestyle=infer_lifestyle(
                    profile_a.get("sleep_schedule"), profile_a.get("noise_tolerance")
                ),
                guests_policy=infer_guests_policy(
                    profile_a.get("security_requirement")
                ),
                substance_use="not_applicable",
            ),
            "profile_b": OutputProfileSchema(
                name=f"Student {profile_b.get('id', 'Unknown')}",
                budget=profile_b.get("budget_PKR"),
                lifestyle=infer_lifestyle(
                    profile_b.get("sleep_schedule"), profile_b.get("noise_tolerance")
                ),
                guests_policy=infer_guests_policy(
                    profile_b.get("security_requirement")
                ),
                substance_use="not_applicable",
            ),
        }

    if not result.get("compatibility_score"):
        total_deduction = 0
        if profile_a.get("budget_PKR") and profile_b.get("budget_PKR"):
            diff = abs(profile_a["budget_PKR"] - profile_b["budget_PKR"])
            max_budget = max(profile_a["budget_PKR"], profile_b["budget_PKR"])
            total_deduction += (
                min(int((diff / max_budget) * 100), 20) if max_budget > 0 else 0
            )
        a_lifestyle = infer_lifestyle(
            profile_a.get("sleep_schedule"), profile_a.get("noise_tolerance")
        )
        b_lifestyle = infer_lifestyle(
            profile_b.get("sleep_schedule"), profile_b.get("noise_tolerance")
        )
        if a_lifestyle and b_lifestyle and a_lifestyle != b_lifestyle:
            total_deduction += 30
        a_guests = infer_guests_policy(profile_a.get("security_requirement"))
        b_guests = infer_guests_policy(profile_b.get("security_requirement"))
        if a_guests and b_guests and a_guests != b_guests:
            total_deduction += 25
        # Add other mismatch checks if needed
        compatibility_score = max(0, min(100, 100 - total_deduction))
        result["compatibility_score"] = compatibility_score
        result["profile_a"] = OutputProfileSchema(
            name=f"Student {profile_a.get('id', 'Unknown')}",
            budget=profile_a.get("budget_PKR"),
            lifestyle=a_lifestyle,
            guests_policy=a_guests,
            substance_use="not_applicable",
        )
        result["profile_b"] = OutputProfileSchema(
            name=f"Student {profile_b.get('id', 'Unknown')}",
            budget=profile_b.get("budget_PKR"),
            lifestyle=b_lifestyle,
            guests_policy=b_guests,
            substance_use="not_applicable",
        )
        result["detected_conflicts"] = []
        if total_deduction > 0:
            if diff / max_budget * 100 > 50 and max_budget > 0:
                result["detected_conflicts"].append(
                    {"type": "budget_disparity", "severity": "high", "confidence": 88}
                )
            if a_lifestyle and b_lifestyle and a_lifestyle != b_lifestyle:
                result["detected_conflicts"].append(
                    {"type": "lifestyle_mismatch", "severity": "high", "confidence": 85}
                )
            if a_guests and b_guests and a_guests != b_guests:
                result["detected_conflicts"].append(
                    {"type": "guest_policy", "severity": "high", "confidence": 80}
                )

    return result


def infer_lifestyle(
    sleep_schedule: Optional[str], noise_tolerance: Optional[str]
) -> Optional[str]:
    if not sleep_schedule or not noise_tolerance:
        return None
    if "night_owl" in sleep_schedule.lower() or "high" in noise_tolerance.lower():
        return "social"
    if "early" in sleep_schedule.lower() or "low" in noise_tolerance.lower():
        return "quiet"
    return "relaxed"


def infer_guests_policy(security_requirement: Optional[str]) -> Optional[str]:
    if not security_requirement:
        return None
    if "female_only_high_security" in security_requirement.lower():
        return "no_overnight_guests"
    if "flexible_mixed_housing_ok" in security_requirement.lower():
        return "open_to_guests"
    return "moderate"


async def score_all_combinations() -> List[dict]:
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(_file_)))
    profiles_path = os.path.join(root_dir, "data", "profiles.json")
    if not os.path.exists(profiles_path):
        print(
            f"❌ profiles.json not found at {profiles_path}. Please run the ProfileReader agent first."
        )
        print(
            f"Tip: Ensure 'data/data.json' exists and run 'uv run agents_workflow/profile_reader.py'."
        )
        return []

    print(f"Loading profiles from {profiles_path}...")
    with open(profiles_path, "r", encoding="utf-8") as f:
        profiles = json.load(f)

    results = []
    for i, profile_a in enumerate(profiles):
        for j, profile_b in enumerate(profiles):
            if i < j:
                result = await score_compatibility(profile_a, profile_b)
                results.append(result)
    return results


# ---------------- Run ----------------
if __name__ == "__main__":
    results = asyncio.run(score_all_combinations())
    if results:
        for result in sorted(
            results, key=lambda x: x.get("compatibility_score", 0), reverse=True
        )[:3]:
            print("✅ Compatibility result:")
            print(json.dumps(result, indent=2))
    else:
        print("❌ No compatibility results generated.")