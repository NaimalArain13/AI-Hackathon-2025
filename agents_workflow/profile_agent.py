from agents import Agent
from schemas.schema import ProfileSchema
from confiig.config import MODEL

profile_agent = Agent(
    name="ProfileReader",
    model=MODEL,
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