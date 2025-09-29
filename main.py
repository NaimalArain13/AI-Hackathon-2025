import os
import json
import uvicorn
import logging
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List, Optional
from utils.agent_runners import AgentRunners

app = FastAPI(title="aRoom Matcher — Minimal API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

logger = logging.getLogger("uvicorn.error")


# Simple compatibility scoring without AI
def calculate_simple_score(profile_a: dict, profile_b: dict) -> int:
    """Calculate compatibility score between two profiles (0-100)"""
    score = 0
    
    # City match (30 points)
    if profile_a.get("city") == profile_b.get("city"):
        score += 30
        
        # Area proximity bonus (10 points if same city)
        if profile_a.get("area") == profile_b.get("area"):
            score += 10
    
    # Budget proximity (20 points)
    budget_a = profile_a.get("budget_PKR", 0)
    budget_b = profile_b.get("budget_PKR", 0)
    if budget_a and budget_b:
        budget_diff = abs(budget_a - budget_b)
        if budget_diff < 2000:
            score += 20
        elif budget_diff < 5000:
            score += 10
        elif budget_diff < 8000:
            score += 5
    
    # Sleep schedule match (15 points)
    sleep_a = str(profile_a.get("sleep_schedule", "")).lower()
    sleep_b = str(profile_b.get("sleep_schedule", "")).lower()
    if sleep_a == sleep_b:
        score += 15
    
    # Cleanliness match (15 points)
    clean_a = str(profile_a.get("cleanliness", "")).lower()
    clean_b = str(profile_b.get("cleanliness", "")).lower()
    if clean_a == clean_b:
        score += 15
    
    # Noise tolerance (10 points)
    noise_a = str(profile_a.get("noise_tolerance", "")).lower()
    noise_b = str(profile_b.get("noise_tolerance", "")).lower()
    if noise_a == noise_b:
        score += 10
    
    return min(score, 100)


def detect_red_flags(profile_a: dict, profile_b: dict) -> List[str]:
    """Detect potential red flags between two profiles"""
    flags = []
    
    # Sleep schedule mismatch
    sleep_a = str(profile_a.get("sleep_schedule", "")).lower()
    sleep_b = str(profile_b.get("sleep_schedule", "")).lower()
    if ("night" in sleep_a or "owl" in sleep_a) and "early" in sleep_b:
        flags.append("sleep_mismatch")
    elif "early" in sleep_a and ("night" in sleep_b or "owl" in sleep_b):
        flags.append("sleep_mismatch")
    
    # Budget disparity
    budget_a = profile_a.get("budget_PKR", 0)
    budget_b = profile_b.get("budget_PKR", 0)
    if budget_a and budget_b:
        if abs(budget_a - budget_b) > 10000:
            flags.append("budget_disparity")
    
    # Cleanliness mismatch
    clean_a = str(profile_a.get("cleanliness", "")).lower()
    clean_b = str(profile_b.get("cleanliness", "")).lower()
    if "high" in clean_a and "low" in clean_b:
        flags.append("cleanliness_mismatch")
    elif "low" in clean_a and "high" in clean_b:
        flags.append("cleanliness_mismatch")
    
    return flags


def generate_wingman_advice(profile: dict, match: dict) -> str:
    """Generate detailed, conversational advice for a match"""
    advice_parts = []
    
    # Opening assessment based on score
    score = match.get("score", 0)
    match_data = match.get("short", {})
    
    if score >= 80:
        advice_parts.append("Great news! This looks like a highly compatible match with strong alignment on key lifestyle factors.")
    elif score >= 60:
        advice_parts.append("This is a promising match with solid compatibility in several important areas, though there are a few things to discuss upfront.")
    else:
        advice_parts.append("This match presents some challenges that will require honest communication and clear boundaries from the start.")
    
    # Analyze specific compatibility factors
    red_flags = match.get("red_flags", [])
    
    if "sleep_mismatch" in red_flags:
        advice_parts.append("Sleep schedules differ significantly between you two. Consider discussing quiet hours (perhaps 11pm-8am as a baseline), using white noise machines, and ideally choosing bedrooms on opposite sides of the apartment if possible. This incompatibility can be managed with mutual respect and clear expectations.")
    
    if "budget_disparity" in red_flags:
        advice_parts.append("There's a notable budget difference that could lead to tension around shared expenses. Before moving in, have a transparent conversation about how you'll split rent, utilities, groceries, and household supplies. Consider whether you'll divide costs 50/50 or proportionally based on income. Getting this sorted early prevents awkward money conversations later.")
    
    if "cleanliness_mismatch" in red_flags:
        advice_parts.append("Your cleanliness standards appear misaligned, which is actually one of the most common sources of roommate conflict. Be proactive: create a specific cleaning schedule with assigned responsibilities (who cleans what, and how often), discuss expectations for shared spaces versus personal rooms, and agree on consequences if someone doesn't hold up their end. A cleaning rota posted in the kitchen can work wonders.")
    
    # Highlight positive factors
    if profile.get("city") == match_data.get("city"):
        if profile.get("area") == match_data.get("area"):
            advice_parts.append("You're both in the same neighborhood, which is fantastic for convenience and makes it easy to view properties together.")
        else:
            advice_parts.append("Being in the same city simplifies logistics significantly, from apartment hunting to coordinating move-in dates.")
    
    # Check budget proximity for positive reinforcement
    budget_a = profile.get("budget_PKR", 0)
    budget_b = match_data.get("budget_PKR", 0)
    if budget_a and budget_b and abs(budget_a - budget_b) < 3000:
        advice_parts.append("Your budgets are closely aligned, which means you'll likely be looking at similar property options and won't have disagreements about affordability.")
    
    # Check lifestyle alignments
    if profile.get("sleep_schedule") == match_data.get("sleep_schedule"):
        advice_parts.append("Matching sleep schedules is a huge plus - you won't be disturbing each other during your active hours.")
    
    if profile.get("cleanliness") == match_data.get("cleanliness"):
        advice_parts.append("You share similar cleanliness standards, which eliminates one of the most common friction points between roommates.")
    
    # Closing recommendation
    if not red_flags and score >= 70:
        advice_parts.append("Overall, this pairing has strong fundamentals with no major red flags. I'd recommend setting up a casual coffee meeting to discuss house rules, lifestyle expectations, and gauge personal chemistry before committing.")
    elif red_flags:
        advice_parts.append("While there are some compatibility concerns flagged above, many successful roommate arrangements work despite these differences. The key is addressing these topics head-on before signing any lease. Consider a trial month if possible, or at minimum, draft a simple roommate agreement covering the areas where you differ.")
    else:
        advice_parts.append("This match could work with the right approach. Meet in person to discuss expectations around guests, noise, cleaning, and shared expenses. Trust your instincts about whether you can communicate openly with this person.")
    
    return " ".join(advice_parts)


@app.post("/api/run-pipeline")
async def run_full_pipeline(
    file: UploadFile = File(None),
    file_path: str = Form(None),
):
    """Parse uploaded profile"""
    temp_file_path = None
    
    if file:
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, file.filename)
        try:
            contents = await file.read()
            with open(temp_file_path, "wb") as f:
                f.write(contents)
            file_path_to_use = temp_file_path
        except Exception as e:
            logger.error(f"Error saving uploaded file: {e}")
            raise HTTPException(status_code=500, detail="Failed to save uploaded file")
    elif file_path:
        file_path_to_use = file_path
        if not os.path.exists(file_path_to_use):
            raise HTTPException(status_code=400, detail=f"file_path not found: {file_path_to_use}")
    else:
        raise HTTPException(status_code=400, detail="Must provide either file upload or file_path")

    try:
        parsed_profile = await AgentRunners.parse_single_profile(file_path_to_use)
        return {"status": "success", "parsed_profile": parsed_profile}
    except Exception as e:
        logger.exception("Error parsing profile")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                logger.warning(f"Could not delete temp file: {e}")


@app.post("/api/match-profile")
async def match_profile(profile: Dict):
    """Find matching roommates from JSON file database"""
    try:
        logger.info(f"Finding matches for profile: {profile.get('id')}")
        
        # Load roommate database from JSON file
        BASE_DIR = os.path.dirname(__file__)
        DB_PATH = os.path.join(BASE_DIR, "data", "profiles.json")
        
        if not os.path.exists(DB_PATH):
            raise HTTPException(status_code=404, detail="Roommate database not found")
        
        with open(DB_PATH, "r", encoding="utf-8") as f:
            all_roommates = json.load(f)
        
        logger.info(f"Loaded {len(all_roommates)} roommates from database")
        
        # Score each roommate
        matches = []
        for roommate in all_roommates:
            # Skip if same ID (don't match with yourself)
            if roommate.get("id") == profile.get("id"):
                continue
            
            # Calculate compatibility score
            score = calculate_simple_score(profile, roommate)
            
            # Detect red flags
            red_flags = detect_red_flags(profile, roommate)
            
            matches.append({
                "roommate_id": roommate.get("id"),
                "score": score,
                "short": {
                    "city": roommate.get("city"),
                    "area": roommate.get("area"),
                    "budget_PKR": roommate.get("budget_PKR"),
                    "cleanliness": roommate.get("cleanliness"),
                    "sleep_schedule": roommate.get("sleep_schedule")
                },
                "red_flags": red_flags
            })
        
        # Sort by score (highest first)
        matches.sort(key=lambda x: x["score"], reverse=True)
        
        # Take top 5 matches
        top_matches = matches[:5]
        
        # Generate simple wingman advice
        wingman_advice = {}
        for match in top_matches:
            advice = generate_wingman_advice(profile, match)
            wingman_advice[match["roommate_id"]] = advice
        
        return {
            "status": "success",
            "matches": top_matches,
            "candidate_count": len(all_roommates),
            "used_fallback": False,
            "wingman": wingman_advice
        }
        
    except Exception as e:
        logger.exception("Error matching profile")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/wingman")
async def run_wingman_get(filtered_matches: str, profiles: Optional[str] = None):
    """
    GET version of wingman endpoint.
    Expects JSON strings in query parameters.
    """
    try:
        filtered_matches_data = json.loads(filtered_matches)
        profiles_data = json.loads(profiles) if profiles else None

        if not filtered_matches_data or not isinstance(filtered_matches_data, list):
            raise HTTPException(
                status_code=400, detail="filtered_matches must be a valid JSON list"
            )

        # Get the first match from the list
        if len(filtered_matches_data) > 0:
            match = filtered_matches_data[0]
            profile = profiles_data[0] if profiles_data and len(profiles_data) > 0 else {}
            
            # Generate advice using the same function
            advice = generate_wingman_advice(profile, match)
            
            return {
                "status": "success",
                "advice": advice
            }
        else:
            return {"status": "success", "advice": "No match data provided"}
            
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid JSON in query parameters: {str(e)}"
        )
    except Exception as e:
        logger.exception("Error running wingman agent")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/wingman")
async def run_wingman_post(filtered_matches: list, profiles: Optional[list] = None):
    """
    POST version of wingman endpoint.
    Expects JSON body with filtered_matches and optional profiles.
    """
    try:
        if not filtered_matches or not isinstance(filtered_matches, list):
            raise HTTPException(
                status_code=400, detail="filtered_matches must be a valid list"
            )

        # Get the first match
        if len(filtered_matches) > 0:
            match = filtered_matches[0]
            profile = profiles[0] if profiles and len(profiles) > 0 else {}
            
            advice = generate_wingman_advice(profile, match)
            
            return {
                "status": "success",
                "advice": advice
            }
        else:
            return {"status": "success", "advice": "No match data provided"}
            
    except Exception as e:
        logger.exception("Error running wingman agent")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)