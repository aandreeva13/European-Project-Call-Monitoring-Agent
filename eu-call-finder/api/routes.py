"""
eu-call-finder/api/routes.py
API Endpoints for EU Call Finder with SSE streaming support
"""

import sys
import os
import importlib.util
import json
import asyncio
import threading
import queue
from typing import Dict, Any, AsyncGenerator
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime objects."""

    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contracts.schemas import CompanyInput, CompanyProfile, ValidationResult, Domain

router = APIRouter()


def load_master_agent():
    """Load the master_agent module using importlib."""
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    module_path = os.path.join(base_path, "2_orchestration", "master_agent.py")

    if not os.path.exists(module_path):
        raise FileNotFoundError(f"Master agent module not found at {module_path}")

    spec = importlib.util.spec_from_file_location("master_agent", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to load module spec from {module_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SearchRequest(BaseModel):
    """Request body for search endpoint."""

    company: CompanyProfile = Field(..., description="Company profile information")
    keywords: list[str] | None = Field(None, description="Optional search keywords")


class FundingCallResponse(BaseModel):
    """Response model for a funding call."""

    id: str
    title: str
    description: str
    deadline: str
    budget: str
    matchScore: float = Field(..., alias="match_score")
    tags: list[str]
    url: str | None = None
    status: str | None = None
    programme: str | None = None
    eligibilityPassed: bool = Field(..., alias="eligibility_passed")
    relevanceScore: float = Field(..., alias="relevance_score")
    recommendation: str | None = None


class SearchResponse(BaseModel):
    """Response model for search endpoint."""

    company_name: str
    search_date: str
    total_calls: int
    calls: list[FundingCallResponse]
    summary: str


@router.post("/search/stream")
async def search_calls_stream(request: Request) -> StreamingResponse:
    """
    Search for EU funding calls with real-time progress updates via SSE.
    """
    print("\n" + "=" * 80)
    print("API ENDPOINT HIT: /api/search/stream")
    print("=" * 80)

    body = await request.body()
    print(f"Received body: {body.decode()[:200]}...")

    try:
        data = json.loads(body)
        request_data = SearchRequest(**data)
        print(f"Parsed request for company: {request_data.company.name}")
    except Exception as e:
        print(f"ERROR parsing request: {e}")

        async def error_stream():
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(error_stream(), media_type="text/event-stream")

    company_input = {
        "company": request_data.company.model_dump(),
        "keywords": request_data.keywords or [],
    }

    # Create thread-safe queue for progress updates
    progress_queue = queue.Queue()
    result_holder = {"result": None, "error": None}

    # Track progress state
    progress_state = {
        "current_agent": "Initializing",
        "safety_done": False,
        "planner_done": False,
        "retriever_done": False,
        "analyzer_done": False,
    }

    def run_workflow_with_progress():
        """Run workflow and emit progress updates."""
        print("\n[THREAD] Workflow thread started!")
        try:
            # Send initial progress
            progress_queue.put(
                {
                    "agent": "Initializing",
                    "progress": 5,
                    "message": "Starting workflow...",
                    "status": "running",
                }
            )
            print("[PROGRESS] Initializing workflow...")

            master_agent = load_master_agent()

            # Import builtins to patch print
            import builtins
            import re

            original_print = builtins.print

            def patched_print(*args, **kwargs):
                """Capture print output and emit progress."""
                message = " ".join(str(arg) for arg in args)

                # Call original print
                original_print(*args, **kwargs)

                # Check for specific progress markers
                if "STEP 1: SAFETY CHECK" in message:
                    progress_queue.put(
                        {
                            "agent": "Safety Guard",
                            "progress": 10,
                            "message": "Validating input for security threats...",
                            "status": "running",
                        }
                    )
                    print("[PROGRESS] Safety Guard started")

                elif "[OK] Safety check passed" in message:
                    progress_state["safety_done"] = True
                    progress_queue.put(
                        {
                            "agent": "Safety Guard",
                            "progress": 15,
                            "message": "Safety check passed",
                            "status": "running",
                        }
                    )
                    print("[PROGRESS] Safety Guard complete")

                elif "STEP 2: PLANNING" in message:
                    progress_queue.put(
                        {
                            "agent": "Smart Planner",
                            "progress": 20,
                            "message": "Analyzing company profile and creating search strategy...",
                            "status": "running",
                        }
                    )
                    print("[PROGRESS] Smart Planner started")

                elif (
                    "[OK] Smart Plan Created" in message
                    or "[OK] Plan created" in message
                ):
                    progress_state["planner_done"] = True
                    progress_queue.put(
                        {
                            "agent": "Smart Planner",
                            "progress": 35,
                            "message": "Search strategy created",
                            "status": "running",
                        }
                    )
                    print("[PROGRESS] Smart Planner complete")

                elif "STEP 3: RETRIEVAL" in message:
                    progress_queue.put(
                        {
                            "agent": "Retriever",
                            "progress": 40,
                            "message": "Scraping EU Funding & Tenders Portal...",
                            "status": "running",
                        }
                    )
                    print("[PROGRESS] Retriever started")

                elif "[OK] Retrieved" in message and "topics" in message:
                    match = re.search(r"(\d+) topics", message)
                    topic_count = match.group(1) if match else "some"
                    progress_state["retriever_done"] = True
                    progress_queue.put(
                        {
                            "agent": "Retriever",
                            "progress": 55,
                            "message": f"Retrieved {topic_count} funding calls",
                            "status": "running",
                        }
                    )
                    print(f"[PROGRESS] Retriever complete ({topic_count} calls)")

                elif "STEP 4: ANALYSIS" in message:
                    progress_queue.put(
                        {
                            "agent": "Analyzer",
                            "progress": 60,
                            "message": "Analyzing and scoring funding calls...",
                            "status": "running",
                        }
                    )
                    print("[PROGRESS] Analyzer started")

                elif "[CHART] Analysis Summary" in message:
                    progress_state["analyzer_done"] = True
                    progress_queue.put(
                        {
                            "agent": "Analyzer",
                            "progress": 80,
                            "message": "Analysis complete",
                            "status": "running",
                        }
                    )
                    print("[PROGRESS] Analyzer complete")

                elif "STEP 5: REPORTING" in message:
                    progress_queue.put(
                        {
                            "agent": "Reporter",
                            "progress": 85,
                            "message": "Generating final report...",
                            "status": "running",
                        }
                    )
                    print("[PROGRESS] Reporter started")

                elif "[OK] Report generated" in message:
                    progress_queue.put(
                        {
                            "agent": "Reporter",
                            "progress": 95,
                            "message": "Report generated",
                            "status": "running",
                        }
                    )
                    print("[PROGRESS] Reporter complete")

            # Patch print
            builtins.print = patched_print

            try:
                print("\n[API] Starting workflow execution...")
                result = master_agent.run_workflow(company_input)
                result_holder["result"] = result
                print("\n[API] Workflow completed successfully")
            finally:
                builtins.print = original_print

        except Exception as e:
            print(f"\n[API] Workflow error: {e}")
            import traceback

            traceback.print_exc()
            result_holder["error"] = str(e)
            progress_queue.put({"type": "error", "data": str(e)})

    # Start workflow in background thread
    workflow_thread = threading.Thread(target=run_workflow_with_progress)
    workflow_thread.start()

    async def event_stream():
        """Stream progress events."""

        # Send initial progress
        yield f"event: progress\ndata: {json.dumps({'agent': 'Initializing', 'progress': 5, 'message': 'Starting workflow...', 'status': 'running'})}\n\n"

        while workflow_thread.is_alive() or not progress_queue.empty():
            try:
                # Check for progress updates (non-blocking)
                while not progress_queue.empty():
                    update = progress_queue.get_nowait()

                    if update.get("type") == "error":
                        yield f"event: error\ndata: {json.dumps({'error': update['data']})}\n\n"
                        return
                    else:
                        yield f"event: progress\ndata: {json.dumps(update)}\n\n"

                # Small delay to prevent busy-waiting
                await asyncio.sleep(0.1)

            except Exception as e:
                print(f"[API] Stream error: {e}")
                continue

        # Workflow completed, send result
        if result_holder["error"]:
            yield f"event: error\ndata: {json.dumps({'error': result_holder['error']})}\n\n"
        elif result_holder["result"]:
            result = result_holder["result"]
            final_report = result.get("final_report") or {}

            # If final_report is still empty/missing, build from analyzed_calls
            if not final_report:
                analyzed_calls = result.get("analyzed_calls", [])
                company_input = result.get("company_input", {})
                company = (
                    company_input.get("company", {})
                    if isinstance(company_input, dict)
                    else {}
                )

                final_report = {
                    "company_profile": {
                        "name": company.get("name", "Unknown"),
                        "type": company.get("type", ""),
                        "country": company.get("country", ""),
                        "employees": company.get("employees", 0),
                        "description": company.get("description", ""),
                        "domains": company.get("domains", []),
                    },
                    "company_summary": {
                        "profile_overview": f"Company profile analysis",
                        "key_strengths": [],
                        "recommended_focus_areas": [],
                    },
                    "overall_assessment": {
                        "total_opportunities": len(analyzed_calls),
                        "high_priority_count": 0,
                        "medium_priority_count": 0,
                        "low_priority_count": 0,
                        "summary_text": f"Found {len(analyzed_calls)} opportunities",
                        "strategic_advice": "Review results below",
                    },
                    "funding_cards": [
                        {
                            "id": call.get("id", str(i)),
                            "title": call.get("title", "Untitled"),
                            "programme": call.get("programme", ""),
                            "description": call.get("raw_data", {}).get(
                                "description", ""
                            )[:300]
                            if call.get("raw_data")
                            else "",
                            "short_summary": call.get("match_summary", ""),
                            "match_percentage": int(
                                call.get("relevance_score", 0) * 10
                            ),
                            "relevance_score": call.get("relevance_score", 0),
                            "eligibility_passed": call.get("eligibility_passed", False),
                            "budget": call.get("budget", "N/A"),
                            "deadline": call.get("deadline", "N/A"),
                            "url": call.get("url", ""),
                            "status": call.get("status", ""),
                            "tags": call.get("keyword_hits", []),
                            "why_recommended": call.get("match_summary", "")[:100],
                            "key_benefits": [],
                            "action_items": [],
                            "success_probability": "medium",
                            "domain_matches": call.get("domain_matches", []),
                            "suggested_partners": call.get("suggested_partners", []),
                        }
                        for i, call in enumerate(analyzed_calls)
                    ],
                    "top_recommendations": [],
                    "total_calls": len(analyzed_calls),
                    "report_type": "fallback_direct",
                    "generated_at": datetime.now().isoformat(),
                }

            # Return the complete report structure
            final_result = {
                "company_profile": final_report.get("company_profile", {}),
                "company_summary": final_report.get("company_summary", {}),
                "overall_assessment": final_report.get("overall_assessment", {}),
                "funding_cards": final_report.get("funding_cards", []),
                "top_recommendations": final_report.get("top_recommendations", []),
                "total_calls": final_report.get("total_calls", 0),
                "report_type": final_report.get("report_type", "unknown"),
                "generated_at": final_report.get(
                    "generated_at", datetime.now().isoformat()
                ),
            }

            # Ensure all datetime objects are converted to strings
            def convert_datetime(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                elif isinstance(obj, dict):
                    return {k: convert_datetime(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_datetime(item) for item in obj]
                return obj

            final_result = convert_datetime(final_result)

            yield f"event: complete\ndata: {json.dumps(final_result, cls=DateTimeEncoder)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/search", response_model=SearchResponse)
async def search_calls(request: Request) -> SearchResponse:
    """
    Search for EU funding calls matching a company profile (non-streaming).
    """
    body = await request.body()
    print("\n" + "=" * 80)
    print("INCOMING REQUEST")
    print("=" * 80)
    print(f"Raw body: {body.decode()}")
    print("=" * 80 + "\n")

    try:
        data = json.loads(body)
        print(f"Parsed JSON: {json.dumps(data, indent=2)}")
    except json.JSONDecodeError as e:
        print(f"JSON Parse Error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

    try:
        request_data = SearchRequest(**data)
        print(f"\nValidation passed!")
        print(f"Company name: {request_data.company.name}")
        print(f"Company type: {request_data.company.type}")
        print(f"Domains: {[d.name for d in request_data.company.domains]}")
    except Exception as e:
        print(f"\nValidation Error: {e}")
        raise HTTPException(status_code=422, detail=f"Validation error: {str(e)}")

    try:
        print("\nLoading master agent...")
        master_agent = load_master_agent()
        print("Master agent loaded successfully")

        company_input = {
            "company": request_data.company.model_dump(),
            "keywords": request_data.keywords or [],
        }

        print(f"\nStarting workflow with company: {company_input['company']['name']}")
        print("=" * 80)

        result = master_agent.run_workflow(company_input)

        print("\n" + "=" * 80)
        print("WORKFLOW COMPLETED")
        print(f"Status: {result.get('workflow_status')}")
        print(f"Analyzed calls: {len(result.get('analyzed_calls', []))}")
        print("=" * 80 + "\n")

        if result.get("workflow_status") == "failed":
            raise HTTPException(
                status_code=400, detail=result.get("error_message", "Workflow failed")
            )

        # Extract data from final_report
        final_report = result.get("final_report", {})
        funding_cards = final_report.get("funding_cards", [])
        company_data = result.get("company_input", {}).get("company", {})

        # Transform cards to response format
        calls = []
        for card in funding_cards:
            calls.append(
                FundingCallResponse(
                    id=card.get("id", "unknown"),
                    title=card.get("title", "Untitled"),
                    description=card.get("short_summary", "No description available"),
                    deadline=card.get("deadline", "N/A"),
                    budget=card.get("budget", "N/A"),
                    match_score=card.get("match_percentage", 0),
                    tags=card.get("tags", []),
                    url=card.get("url"),
                    status=card.get("status"),
                    programme=card.get("programme"),
                    eligibility_passed=card.get("eligibility_passed", False),
                    relevance_score=card.get("relevance_score", 0),
                    recommendation=card.get("success_probability"),
                )
            )

        # Sort by match score (highest first)
        calls.sort(key=lambda x: x.match_score, reverse=True)

        return SearchResponse(
            company_name=company_data.get("name", "Unknown"),
            search_date=datetime.now().isoformat(),
            total_calls=len(calls),
            calls=calls,
            summary=f"Found {len(calls)} relevant EU funding calls matching your profile.",
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "search"}
