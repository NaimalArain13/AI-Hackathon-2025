import os
import uvicorn
import logging
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from utils.agent_runners import AgentRunners

app = FastAPI(title="aRoom Matcher — Minimal API (pipeline + wingman)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

logger = logging.getLogger("uvicorn.error")


class FilePathIn(BaseModel):
    file_path: str


@app.post("/api/run-pipeline")
async def run_full_pipeline(
    file: Optional[UploadFile] = File(None),
    file_path: Optional[str] = Form(None),
):
    """
    Accepts either a file upload or a form field 'file_path' as string.
    Parses the uploaded profile and returns structured data.
    """
    temp_file_path = None
    
    if file:
        # Save uploaded file to temp location
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, file.filename)
        try:
            contents = await file.read()
            with open(temp_file_path, "wb") as f:
                f.write(contents)
            file_path_to_use = temp_file_path
            logger.info(f"Saved uploaded file to: {temp_file_path}")
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
        # Parse the single uploaded profile using the new method
        logger.info(f"Starting profile parsing for: {file_path_to_use}")
        parsed_profile = await AgentRunners.parse_single_profile(file_path_to_use)
        
        logger.info(f"Successfully parsed profile: {parsed_profile.get('id', 'unknown')}")
        
        # Return in the format frontend expects
        return {
            "status": "success",
            "parsed_profile": parsed_profile
        }
            
    except Exception as e:
        logger.exception(f"Error parsing profile from {file_path_to_use}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temp file if it was uploaded
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"Cleaned up temp file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Could not delete temp file: {e}")


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

        advice = await AgentRunners.run_wingman_agent(
            filtered_matches, profiles
        )
        return {"status": "success", "advice": advice}
    except Exception as e:
        logger.exception("Error running wingman agent")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/wingman")
async def run_wingman_get(filtered_matches: str, profiles: Optional[str] = None):
    """
    GET version of wingman endpoint.
    Expects JSON strings in query parameters.
    """
    import json

    try:
        filtered_matches_data = json.loads(filtered_matches)
        profiles_data = json.loads(profiles) if profiles else None

        if not filtered_matches_data or not isinstance(filtered_matches_data, list):
            raise HTTPException(
                status_code=400, detail="filtered_matches must be a valid JSON list"
            )

        advice = await AgentRunners.run_wingman_agent(
            filtered_matches_data, profiles_data
        )
        return {"status": "success", "advice": advice}
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid JSON in query parameters: {str(e)}"
        )
    except Exception as e:
        logger.exception("Error running wingman agent")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)