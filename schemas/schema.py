from pydantic import BaseModel
from typing import Optional

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