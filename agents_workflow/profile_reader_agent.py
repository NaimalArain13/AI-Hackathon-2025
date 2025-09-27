# profile_reader.py
import os
import json
import asyncio
from dotenv import load_dotenv, find_dotenv
from pydantic import BaseModel
from typing import Optional

from agents import (
    Agent,
    Runner,
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    set_tracing_disabled,
    SQLiteSession,
)

# ---------------- Setup ----------------
load_dotenv(find_dotenv())
set_tracing_disabled(True)

API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")

client_provider = AsyncOpenAI(
    api_key=API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",  # Gemini
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

# ---------------- Agent ----------------
profileagent = Agent(
    name="ProfileReader",
    model=Model,
    instructions="""
    You are ProfileReader Agent that extracts structured data from roommate profile descriptions.
    
    You will receive messy roommate ads in Urdu/English mix and need to extract these attributes:
    - id: unique identifier (will be provided in context)
    - city: city name (Karachi, Lahore, Islamabad, etc.)
    - area: specific area/locality within city
    - budget_PKR: budget in Pakistani Rupees (extract numbers, convert to integer)
    - sleep_schedule: categorize as "early" | "normal" | "night_owl" | "flexible"
    - cleanliness: categorize as "high" | "medium" | "low" 
    - noise_tolerance: categorize as "low" | "medium" | "high"
    - study_habits: describe study preferences/habits
    - food_pref: food preferences (vegetarian, non-vegetarian, etc.)
    
    If a field is missing, leave it as null.
    """,
    output_type=ProfileSchema, 
)

runner = Runner() 


# ---------------- Main Flow ----------------
async def run_profile_reader():
    try:
        BASE_DIR = os.path.dirname(os.path.dirname(__file__))
        DATA_PATH = os.path.join(BASE_DIR, "data", "data.json")
        
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            raw_profiles = json.load(f)

        print(f"📖 Processing {len(raw_profiles)} raw profiles...")

        structured_profiles = []

        for i, profile_data in enumerate(raw_profiles):
            try:
                message = f"""
                Extract and normalize information from this roommate profile:
                {profile_data['raw_profile_text']}
                
                Profile ID: {profile_data['id']}
                """

                resp = await runner.run(
                   profileagent,            
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

                # Fallback normalization
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

        with open("data/profiles_datas.json", "w", encoding="utf-8") as f:
            json.dump(structured_profiles, f, indent=2, ensure_ascii=False)

        print("✅ Structured profiles saved to data/profiles.json")
        return structured_profiles

    except FileNotFoundError:
        print("❌ Error: data/data.json not found.")
        return []
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return []


# ---------------- Normalizers ----------------
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


if __name__ == "__main__":
    asyncio.run(run_profile_reader())
