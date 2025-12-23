"""
Intelligent Bot Builder API - Endpoints for AI-powered bot creation.
Provides REST API for creating bots from natural language descriptions.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, List, Any
from pathlib import Path
import logging
import json
from ..intelligent_bot_builder import create_bot_from_natural_language

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/intelligent-bots", tags=["intelligent-bots"])


@router.get("/dashboard", response_class=HTMLResponse)
async def get_intelligent_dashboard():
    """
    Serve the intelligent bot builder dashboard.
    Modern, user-friendly interface for bot creation without coding.
    """
    dashboard_file = Path(__file__).parent / "dashboard_ui.html"
    if dashboard_file.exists():
        return dashboard_file.read_text()
    else:
        return """
        <h1>Dashboard Not Found</h1>
        <p>The intelligent dashboard UI could not be found.</p>
        <p><a href="/docs">View API Documentation</a></p>
        """



@router.post("/create-from-description")
async def create_bot_from_natural_language_endpoint(request_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a bot from a natural language description.

    No coding required! Just describe what you want your bot to do.

    Request body:
    {
        "description": "Monitor a database table for new records every 5 seconds and send them to our API"
    }
    """
    try:
        description = request_body.get("description", "")
        if not description:
            raise ValueError("description field is required")

        # Get bots directory
        bots_dir = Path(__file__).parent.parent.parent / "bots"

        # Create bot
        result = await create_bot_from_natural_language(
            description,
            bots_dir
        )

        logger.info(f"Created bot: {result['name']}")

        return {
            "success": True,
            "bot_name": result['name'],
            "bot_path": result['path'],
            "message": f"✨ Bot '{result['name']}' created successfully!",
            "created_files": result['files_created'],
            "ready_to_deploy": result['ready_to_deploy'],
            "task_type": result['task_type'],
            "complexity": result['complexity'],
            "features": result['features'],
        }

    except Exception as e:
        logger.error(f"Error creating bot: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


@router.post("/quick-create")


@router.post("/quick-create")
async def quick_create_bot(request_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Quick bot creation with simpler parameters.

    Request body:
    {
        "description": "Monitor orders database"
    }
    """
    description = request_body.get("description", "")
    if not description:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": "description is required"}
        )

    return await create_bot_from_natural_language_endpoint({"description": description})


@router.get("/templates")
async def get_bot_templates() -> Dict[str, Any]:
    """
    Get available bot templates and their descriptions.
    Users can choose from these or use AI to auto-select.
    """
    return {
        "templates": [
            {
                "id": "worker",
                "name": "Worker Bot",
                "icon": "⚙️",
                "description": "Process tasks, transform data, or execute calculations",
                "best_for": ["data processing", "transformations", "calculations"],
                "complexity": "moderate",
            },
            {
                "id": "collector",
                "name": "Collector Bot",
                "icon": "📦",
                "description": "Gather and collect data from multiple sources",
                "best_for": ["data collection", "scraping", "aggregation"],
                "complexity": "moderate",
            },
            {
                "id": "api",
                "name": "API Bot",
                "icon": "🌐",
                "description": "Make API calls and handle external integrations",
                "best_for": ["API integration", "webhooks", "data sync"],
                "complexity": "moderate",
            },
            {
                "id": "analyzer",
                "name": "Analyzer Bot",
                "icon": "📊",
                "description": "Analyze data and generate insights",
                "best_for": ["data analysis", "reporting", "metrics"],
                "complexity": "advanced",
            },
            {
                "id": "monitor",
                "name": "Monitor Bot",
                "icon": "👁️",
                "description": "Monitor systems and send alerts",
                "best_for": ["monitoring", "alerting", "health checks"],
                "complexity": "simple",
            },
        ],
        "total": 5,
        "message": "Choose a template or describe what you want - we'll handle the rest!"
    }


@router.get("/examples")
async def get_bot_examples() -> Dict[str, List[Dict[str, str]]]:
    """
    Get example bot descriptions and what they create.
    Helps users understand how to describe bots effectively.
    """
    return {
        "examples": [
            {
                "description": "Monitor orders database table for new records every 5 minutes and forward them to the fulfillment API",
                "would_create": "API Integration Bot",
                "features": ["database monitoring", "API calls", "error handling"]
            },
            {
                "description": "Process CSV files, clean the data by removing duplicates and invalid entries, then save to PostgreSQL",
                "would_create": "Data Processing Bot",
                "features": ["file handling", "data cleaning", "database storage"]
            },
            {
                "description": "Collect weather data from OpenWeather API every hour and store in database for historical analysis",
                "would_create": "Data Collector Bot",
                "features": ["API integration", "scheduling", "data storage"]
            },
            {
                "description": "Analyze sales data daily and send email reports with insights and charts to management team",
                "would_create": "Analytics Bot",
                "features": ["data analysis", "reporting", "email notifications"]
            },
            {
                "description": "Monitor system health every minute, check CPU/memory/disk usage and create alerts if any exceed 80%",
                "would_create": "Monitoring Bot",
                "features": ["health monitoring", "alerting", "continuous operation"]
            },
        ],
        "message": "These are examples of how to describe bots. Be as detailed as possible!"
    }


@router.get("/help")
async def get_help() -> Dict[str, Any]:
    """
    Get help on how to describe bots for the AI to understand.
    """
    return {
        "help": {
            "title": "How to Write Great Bot Descriptions",
            "tips": [
                "Be specific about what data the bot processes",
                "Include information about frequency (daily, every 5 minutes, on-demand, etc.)",
                "Mention data sources (database, API, files, etc.)",
                "Describe the output or result (save, send email, call API, etc.)",
                "Note any special requirements (error handling, notifications, etc.)",
            ],
            "template": """
I want a bot that:
- Runs: [when/how often]
- Gets data from: [source]
- Does: [action/transformation]
- Outputs to: [destination]
- Handles errors by: [error handling]
            """.strip(),
            "examples": [
                "Monitor the orders table every 5 seconds and send new orders to our fulfillment API",
                "Every night at midnight, fetch sales data from our database and email a summary report to management",
                "When a file is uploaded, process it to remove duplicates and save clean data to PostgreSQL",
                "Continuously monitor server health and alert via Slack if CPU exceeds 80%",
            ]
        }
    }


@router.post("/test-description")
async def test_bot_description(request_body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Test a bot description without creating it.
    Returns what bot would be created based on the description.

    Request body:
    {
        "description": "Monitor orders database"
    }
    """
    try:
        description = request_body.get("description", "")
        if not description:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "description is required"}
            )

        from ..intelligent_bot_builder import NLPBotInterpreter

        interpreter = NLPBotInterpreter()
        requirements = await interpreter.interpret(description)

        return {
            "success": True,
            "analysis": {
                "name": requirements.name,
                "purpose": requirements.purpose,
                "task_type": requirements.primary_task,
                "frequency": requirements.frequency,
                "complexity": requirements.complexity,
                "input_type": requirements.input_type,
                "output_type": requirements.output_type,
                "features": requirements.special_features,
                "recommendation": f"Based on your description, we'd create a {requirements.complexity} {requirements.primary_task} bot that runs {requirements.frequency}.",
            }
        }
    except Exception as e:
        logger.error(f"Error testing description: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )


# Export router
__all__ = ['router']
