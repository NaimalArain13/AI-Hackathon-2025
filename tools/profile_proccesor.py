import json
import asyncio
import os
from agents import Runner, SQLiteSession
from confiig.config import DATA_PATH, OUTPUT_PATH
from agents_workflow.profile_agent import profile_agent

def normalize_sleep_schedule(value):
    if not value:
        return None
    v = value.lower()
    if "night" in v or "late" in v or "1am" in v:
        return "night_owl"
    elif "early" in v or "riser" in v:
        return "early"
    elif "flexible" in v or "chill" in v:
        return "flexible"
    else:
        return "normal"

def normalize_cleanliness(value):
    if not value:
        return None
    v = value.lower()
    if "tidy" in v or "saaf" in v:
        return "high"
    elif "messy" in v or "gandey" in v:
        return "low"
    else:
        return "medium"

def normalize_noise_tolerance(value):
    if not value:
        return None
    v = value.lower()
    if "quiet" in v:
        return "low"
    elif "moderate" in v or "average" in v:
        return "medium"
    elif "loud" in v or "high" in v:
        return "high"
    else:
        return "medium"

async def run_profile_reader():
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            raw_profiles = json.load(f)

        print(f"📖 Processing {len(raw_profiles)} raw profiles...")
        runner = Runner()
        structured_profiles = []

        for i, profile_data in enumerate(raw_profiles):
            try:
                message = f"""
                Extract and normalize information from this roommate profile:
                {profile_data['raw_profile_text']}
                
                Profile ID: {profile_data['id']}
                """

                resp = await runner.run(
                    profile_agent,
                    message,
                    session=SQLiteSession("trace.db")
                )
                if hasattr(resp, "output"):
                    profile_dict = resp.output.dict()
                elif hasattr(resp, "final_output"):
                    profile_dict = resp.final_output.dict()
                else:
                    profile_dict = {}

                profile_dict["id"] = profile_data["id"]

                fallback_mapping = {
                    "city": profile_data.get("city"),
                    "area": profile_data.get("area"),
                    "budget_PKR": profile_data.get("budget_PKR"),
                    "sleep_schedule": normalize_sleep_schedule(profile_data.get("sleep_schedule")),
                    "cleanliness": normalize_cleanliness(profile_data.get("cleanliness")),
                    "noise_tolerance": normalize_noise_tolerance(profile_data.get("noise_tolerance")),
                    "study_habits": profile_data.get("study_habits"),
                    "food_pref": profile_data.get("food_pref"),
                }

                for key, fallback_value in fallback_mapping.items():
                    if not profile_dict.get(key) and fallback_value:
                        profile_dict[key] = fallback_value

                structured_profiles.append(profile_dict)
                print(f"✅ Processed profile {i+1}/{len(raw_profiles)}: {profile_data['id']}")
 
                await asyncio.sleep(4)

            except Exception as e:
                print(f"❌ Error processing profile {profile_data['id']}: {e}")

        os.makedirs("data", exist_ok=True)
        with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(structured_profiles, f, indent=2, ensure_ascii=False)

        print("✅ Structured profiles saved to data/profiles.json")
        return structured_profiles

    except FileNotFoundError:
        print("❌ Error: data/data.json not found.")
        return []
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return []

if __name__ == "__main__":
    asyncio.run(run_profile_reader())