import asyncio
import json
import sys
import os
from typing import Dict, List, Optional

# Add the parent directory to Python path to import from root level
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all agent runners from root level
from profile_reader import run_profile_reader
from compatibility_agent import score_compatibility, score_all_combinations
from wingMan import run_wingman_short_advice_demo

class AgentRunners:
    """Centralized runner for all agents"""
    
    @staticmethod
    async def run_profile_reader_agent():
        """Run profile reader agent"""
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
                        "recommendation": "Discuss cost sharing"
                    }
                ],
                "overall_assessment": {
                    "recommendation": "PROCEED WITH CAUTION",
                    "risk_level": "MEDIUM",
                    "viability_score": 70
                }
            }
        except Exception as e:
            print(f"Error in red flag agent: {e}")
            return {"error": str(e)}
    
    @staticmethod
    async def run_wingman_agent(red_flag_report: dict):
        """Run wingman advice agent"""
        try:
            # For now, we'll use the demo function
            await run_wingman_short_advice_demo()
            return {
                "advice": "Based on the analysis, this match has some challenges but can work with proper communication and boundary setting.",
                "recommendation": "Proceed with caution and establish clear house rules."
            }
        except Exception as e:
            print(f"Error in wingman agent: {e}")
            return {"error": str(e)}
    
    @staticmethod
    async def run_full_pipeline(profile_a: dict, profile_b: dict):
        """Run complete roommate matching pipeline"""
        try:
            # Step 1: Get compatibility score
            compatibility = await AgentRunners.run_compatibility_agent(profile_a, profile_b)
            
            # Step 2: Analyze red flags
            red_flags = await AgentRunners.run_red_flag_agent(compatibility)
            
            # Step 3: Get wingman advice
            advice = await AgentRunners.run_wingman_agent(red_flags)
            
            return {
                "compatibility": compatibility,
                "red_flags": red_flags,
                "advice": advice
            }
        except Exception as e:
            print(f"Error in full pipeline: {e}")
            return {"error": str(e)}