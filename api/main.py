"""
GridPulse - Backend REST API
Member 3 Integration: Recommendation and Energy Savings Simulation Services

Lightweight Starlette REST API connecting the React dashboard with Member 3's
tested Python recommendation and simulation engines.
"""

import math
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional

# Ensure project root is available on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from recommendation.appliance_recommender import (
    generate_household_recommendation_report,
)
from recommendation.savings_simulator import (
    simulate_household_savings,
)


async def health_check(request: Request) -> JSONResponse:
    """
    Endpoint A: GET /api/health
    Returns service health status and version.
    """
    return JSONResponse({
        "status": "ok",
        "service": "GRID_PULSE Backend API",
        "version": "1.0.0",
    }, status_code=200)


async def recommendations_endpoint(request: Request) -> JSONResponse:
    """
    Endpoint B: POST /api/recommendations
    Accepts household appliances and electricity rate.
    Returns complete recommendation report with rankings and hypothetical suggestions.
    """
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(
            {"error": "Invalid JSON format in request body."},
            status_code=400,
        )

    if not isinstance(payload, dict):
        return JSONResponse(
            {"error": "Request body must be a JSON object."},
            status_code=400,
        )

    appliances = payload.get("appliances")
    if appliances is None or not isinstance(appliances, list):
        return JSONResponse(
            {"error": "Field 'appliances' is required and must be a list of appliance records."},
            status_code=400,
        )

    electricity_rate = payload.get("electricity_rate")

    try:
        report = generate_household_recommendation_report(
            appliances=appliances,
            electricity_rate=electricity_rate,
        )
        return JSONResponse(report, status_code=200)
    except ValueError as exc:
        return JSONResponse(
            {"error": str(exc)},
            status_code=400,
        )
    except Exception as exc:
        return JSONResponse(
            {"error": f"Internal recommendation calculation error: {str(exc)}"},
            status_code=500,
        )


async def simulate_endpoint(request: Request) -> JSONResponse:
    """
    Endpoint C: POST /api/simulate
    Accepts baseline appliances, user-defined usage adjustments, and electricity rate.
    Returns simulated consumption, net kWh savings, cost savings, and safety warnings.
    """
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(
            {"error": "Invalid JSON format in request body."},
            status_code=400,
        )

    if not isinstance(payload, dict):
        return JSONResponse(
            {"error": "Request body must be a JSON object."},
            status_code=400,
        )

    appliances = payload.get("appliances")
    if appliances is None or not isinstance(appliances, list):
        return JSONResponse(
            {"error": "Field 'appliances' is required and must be a list of appliance records."},
            status_code=400,
        )

    adjustments = payload.get("adjustments", [])
    if not isinstance(adjustments, list):
        return JSONResponse(
            {"error": "Field 'adjustments' must be a list of adjustment records if provided."},
            status_code=400,
        )

    electricity_rate = payload.get("electricity_rate")

    try:
        result = simulate_household_savings(
            baseline_appliances=appliances,
            adjustments=adjustments,
            electricity_rate=electricity_rate,
        )
        return JSONResponse(result, status_code=200)
    except ValueError as exc:
        return JSONResponse(
            {"error": str(exc)},
            status_code=400,
        )
    except Exception as exc:
        return JSONResponse(
            {"error": f"Internal simulation calculation error: {str(exc)}"},
            status_code=500,
        )


# API Routes definition
routes = [
    Route("/api/health", health_check, methods=["GET"]),
    Route("/api/recommendations", recommendations_endpoint, methods=["POST"]),
    Route("/api/simulate", simulate_endpoint, methods=["POST"]),
]

# CORS Middleware configured strictly for React Vite dev server
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        allow_credentials=True,
    )
]

# Starlette Application Instance
app = Starlette(routes=routes, middleware=middleware)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
