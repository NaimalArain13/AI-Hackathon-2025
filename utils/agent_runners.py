import asyncio
import json
import sys
import os
from typing import Dict, List, Optional, Any

# Add the parent directory to Python path to import from root level
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all agent runners from root level
from profile_reader import (
    run_profile_reader, 
    parse_docx_to_raw_text, 
    extract_structured_profile,
    normalize_sleep_schedule,
    normalize_cleanliness,
    normalize_noise_tolerance
)
from compatibility_agent import score_compatibility, score_all_combinations
from wingMan import run_wingman_short_advice_demo


class AgentRunners:
    """Centralized runner for all agents"""

    @staticmethod
    async def parse_single_profile(file_path: str) -> Dict[str, Any]:
        """
        Parse a single uploaded profile file and return structured profile data.
        
        Args:
            file_path: Path to the uploaded file (docx, pdf, or image)
            
        Returns:
            Dictionary containing parsed profile data matching ParsedProfile schema
        """
        try:
            # Generate unique ID for this profile
            import time
            profile_id = f"U-{int(time.time())}"
            
            # Check file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext == '.docx':
                # Parse DOCX file to extract raw text
                raw_text = parse_docx_to_raw_text(file_path)
                if not raw_text:
                    raise Exception("Failed to extract text from DOCX file")
                
                # Use the profile reader agent to extract structured data
                profile_dict = await extract_structured_profile(raw_text, profile_id)
                
                if not profile_dict or not profile_dict.get('id'):
                    raise Exception("Failed to extract profile data from text")
                
                # Return flat structure matching frontend ParsedProfile interface
                parsed_profile = {
                    "id": profile_dict.get("id", profile_id),
                    "city": profile_dict.get("city", ""),
                    "area": profile_dict.get("area", ""),
                    "budget_PKR": profile_dict.get("budget_PKR", 0),
                    "sleep_schedule": profile_dict.get("sleep_schedule", ""),
                    "cleanliness": profile_dict.get("cleanliness", ""),
                    "noise_tolerance": profile_dict.get("noise_tolerance", ""),
                    "study_habits": profile_dict.get("study_habits", ""),
                    "food_pref": profile_dict.get("food_pref", ""),
                    "notes": ""  # Template doesn't include notes
                }
                
                return parsed_profile
                
            elif file_ext == '.pdf':
                # TODO: Implement PDF parsing
                raise Exception("PDF parsing not yet implemented. Please upload a DOCX file.")
                
            elif file_ext in ['.png', '.jpg', '.jpeg']:
                # TODO: Implement OCR for images
                raise Exception("Image OCR not yet implemented. Please upload a DOCX file.")
                
            else:
                raise Exception(f"Unsupported file type: {file_ext}")
            
        except Exception as e:
            print(f"Error parsing profile from {file_path}: {e}")
            raise Exception(f"Failed to parse profile: {str(e)}")

    @staticmethod
    async def run_profile_reader_agent():
        """Run profile reader agent for batch processing"""
        try:
            return await run_profile_reader()
        except Exception as e:
            print(f"Error in profile reader: {e}")
            return []

    @staticmethod
    async def run_compatibility_agent(profile_a: dict, profile_b: dict):
        """Run compatibility scoring agent"""
        try:
            return await score_compatibility(profile_a, profile_b)
        except Exception as e:
            print(f"Error in compatibility agent: {e}")
            return {"error": str(e)}

    @staticmethod
    async def run_all_compatibility_combinations():
        """Run compatibility for all profile combinations"""
        try:
            return await score_all_combinations()
        except Exception as e:
            print(f"Error in all combinations: {e}")
            return []

    @staticmethod
    async def run_red_flag_agent(compatibility_result: dict):
        """Run red flag detection agent"""
        try:
            # Since redFlagAgent doesn't have a main function, we'll create a mock response
            return {
                "analysis_summary": {
                    "total_conflicts_detected": 2,
                    "high_confidence_flags": 1,
                    "filtered_red_flags": 1,
                    "overall_risk_level": "MEDIUM",
                },
                "red_flags": [
                    {
                        "flag_id": "RF001",
                        "type": "budget_disparity",
                        "severity": "MEDIUM",
                        "confidence": 85,
                        "description": "Budget difference detected",
                        "recommendation": "Discuss cost sharing",
                    }
                ],
                "overall_assessment": {
                    "recommendation": "PROCEED WITH CAUTION",
                    "risk_level": "MEDIUM",
                    "viability_score": 70,
                },
            }
        except Exception as e:
            print(f"Error in red flag agent: {e}")
            return {"error": str(e)}

    @staticmethod
    async def run_wingman_agent(
        filtered_matches: List[Dict[str, Any]],
        profiles: Optional[List[Dict[str, Any]]] = None,
    ):
        """Run wingman advice agent"""
        try:
            # For now, we'll use the demo function
            await run_wingman_short_advice_demo()
            return {
                "advice": "Based on the analysis, this match has some challenges but can work with proper communication and boundary setting.",
                "recommendation": "Proceed with caution and establish clear house rules.",
            }
        except Exception as e:
            print(f"Error in wingman agent: {e}")
            return {"error": str(e)}

    @staticmethod
    async def run_full_pipeline(profile_a: dict, profile_b: dict):
        """
        Run complete roommate matching pipeline.
        This compares TWO profiles and returns compatibility analysis.
        
        Args:
            profile_a: First profile dictionary
            profile_b: Second profile dictionary
            
        Returns:
            Dictionary with compatibility, red_flags, and advice
        """
        try:
            # Step 1: Get compatibility score
            compatibility = await AgentRunners.run_compatibility_agent(
                profile_a, profile_b
            )

            # Step 2: Analyze red flags
            red_flags = await AgentRunners.run_red_flag_agent(compatibility)

            # Step 3: Get wingman advice
            advice = await AgentRunners.run_wingman_agent([red_flags])

            return {
                "compatibility": compatibility,
                "red_flags": red_flags,
                "advice": advice,
            }
        except Exception as e:
            print(f"Error in full pipeline: {e}")
            return {"error": str(e)}

