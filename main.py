# main.py
import os
import uvicorn
import logging
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Import your AgentRunners (ensure agent_runners.py is in same folder or on PYTHONPATH)
from utils.agent_runners import AgentRunners

app = FastAPI(title="aRoom Matcher — Minimal API (pipeline + wingman)")

# Add CORS middleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Allows all origins
#     allow_credentials=True,
#     allow_methods=["*"],  # Allows all methods
#     allow_headers=["*"],  # Allows all headers
# )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # allow any origin
    allow_methods=["*"],        # allow all methods (POST, GET, OPTIONS, etc.)
    allow_headers=["*"],        # allow all headers
    allow_credentials=False,    # set to True only if you need cookies/auth; see note below
)
logger = logging.getLogger("uvicorn.error")


# ---------- Request models ----------
class FilePathIn(BaseModel):
    file_path: str


class WingmanIn(BaseModel):
    filtered_matches: List[Dict[str, Any]]
    # optional structured profiles, forwarded to wingman if needed
    profiles: Optional[List[Dict[str, Any]]] = None


# ---------- Routes (only two) ----------
@app.post("/api/run-pipeline")
async def run_full_pipeline(payload: FilePathIn):
    """
    Run full pipeline: profile_reader -> compatibility -> red flags -> wingman.
    Expects: {"file_path": "/abs/path/to/uploaded.docx"}
    """
    file_path = payload.file_path
    if not file_path or not isinstance(file_path, str):
        raise HTTPException(status_code=400, detail="file_path is required")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail=f"file_path not found: {file_path}")

    try:
        result = await AgentRunners.run_full_pipeline(file_path)
        return {"status": "success", "result": result}
    except Exception as e:
        logger.exception("Error running full pipeline")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/wingman")
async def run_wingman(filtered_matches: str, profiles: Optional[str] = None):
    """
    Run Wingman stage only.
    Expects query parameters:
    - filtered_matches: JSON string of filtered matches from red-flag stage
    - profiles: Optional JSON string of structured profiles
    """
    try:
        # Parse JSON strings from query parameters
        filtered_matches_data = json.loads(filtered_matches)
        profiles_data = json.loads(profiles) if profiles else None

        if not filtered_matches_data or not isinstance(filtered_matches_data, list):
            raise HTTPException(
                status_code=400, detail="filtered_matches must be a valid JSON list"
            )

        advice = await AgentRunners.run_wingman_agent(
            filtered_matches_data, profiles_data
        )
        return {"status": "success", "count": len(advice), "advice": advice}
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid JSON in query parameters: {str(e)}"
        )
    except Exception as e:
        logger.exception("Error running wingman agent")
        raise HTTPException(status_code=500, detail=str(e))


# ---------- Run server (dev) ----------
if __name__ == "__main__":
    # dev server on port 8000
    uvicorn.run(
        "main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True
    )
