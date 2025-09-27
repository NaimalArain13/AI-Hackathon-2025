from pydantic import BaseModel
from typing import Optional, List

class ProfileSchema(BaseModel):
    id: str
    city: Optional[str] = None
    area: Optional[str] = None
    budget_PKR: Optional[int] = None
    sleep_schedule: Optional[str] = None   # early | normal | night_owl | flexible
    cleanliness: Optional[str] = None      # high | medium | low
    noise_tolerance: Optional[str] = None  # low | medium | high
    study_habits: Optional[str] = None
    food_pref: Optional[str] = None

# ---------------- Schema ----------------
class CompatibilityScore(BaseModel):
    profile_1_id: str
    profile_2_id: str
    score: int  # 0-100
    factors: List[str]
    conflicts: List[str]