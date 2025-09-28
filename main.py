# main.py
import os
import uvicorn
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

# Import your AgentRunners (ensure agent_runners.py is in same folder or on PYTHONPATH)
from utils.agent_runners import AgentRunners

app = FastAPI(title="aRoom Matcher — Minimal API (pipeline + wingman)")
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


@app.post("/api/wingman")
async def run_wingman(payload: WingmanIn):
    """
    Run Wingman stage only.
    Expects:
    {
      "filtered_matches": [...],   # output of red-flag stage
      "profiles": [...]            # optional, structured profiles
    }
    """
    if not payload.filtered_matches or not isinstance(payload.filtered_matches, list):
        raise HTTPException(status_code=400, detail="filtered_matches is required and must be a list")

    try:
        advice = await AgentRunners.run_wingman_agent(payload.filtered_matches, payload.profiles)
        return {"status": "success", "count": len(advice), "advice": advice}
    except Exception as e:
        logger.exception("Error running wingman agent")
        raise HTTPException(status_code=500, detail=str(e))


# ---------- Run server (dev) ----------
if __name__ == "__main__":
    # dev server on port 8000
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)
