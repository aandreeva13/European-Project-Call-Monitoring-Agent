"""
LangGraph State definitions for EU Call Finder.
Defines the complete state structure for the workflow.
"""

from typing import List, Dict, Any, Optional, TypedDict, Annotated
from dataclasses import dataclass, field
from datetime import datetime
import operator


# Type alias for aggregated lists
AggregatedList = Annotated[List[Dict[str, Any]], operator.add]


class WorkflowState(TypedDict):
    """
    Complete state for the EU Call Finder LangGraph workflow.

    This state is passed between all nodes in the graph and accumulates
    information as the workflow progresses.
    """

    # === INPUT ===
    company_input: Optional[Dict[str, Any]]  # Raw company profile input

    # === SAFETY & VALIDATION ===
    safety_check_passed: bool
    validation_result: Optional[Dict[str, Any]]
    validation_errors: List[str]

    # === PLANNING ===
    planner_iterations: int  # Track planner-critic loops
    max_planner_iterations: int  # Prevent infinite loops
    scraper_plan: Optional[Dict[str, Any]]  # Current plan
    plan_approved: bool  # Whether critic approved the plan
    plan_feedback: Optional[str]  # Critic feedback for plan refinement

    # === RETRIEVAL ===
    search_terms: List[str]
    search_query: Dict[str, Any]  # EU API query
    scraped_topics: List[Dict[str, Any]]  # Raw scraped data
    retrieval_errors: List[str]

    # === ANALYSIS ===
    analyzed_calls: List[Dict[str, Any]]  # Calls with scores and analysis
    eligibility_results: List[Dict[str, Any]]
    analysis_errors: List[str]
    analysis_summary: Optional[Dict[str, Any]]  # Reflection results and decision

    # === REPORTING ===
    final_report: Optional[Dict[str, Any]]
    report_format: str  # "json" or "html"

    # === WORKFLOW CONTROL ===
    current_step: str
    workflow_status: str  # "running", "completed", "failed"
    error_message: Optional[str]
    start_time: Optional[str]
    end_time: Optional[str]


@dataclass
class CallMatch:
    """Represents a matched EU funding call with analysis."""

    id: str
    title: str
    url: str
    programme: str
    status: str

    # Scoring
    relevance_score: float = 0.0  # 0-10
    eligibility_passed: bool = False

    # Analysis
    summary: str = ""
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    # Match details
    matched_keywords: List[str] = field(default_factory=list)
    deadline: Optional[str] = None
    budget: Optional[str] = None


@dataclass
class CompanyProfile:
    """Simplified company profile for internal use."""

    name: str
    description: str
    company_type: str  # SME, Large Enterprise, etc.
    country: str
    employees: int
    domains: List[Dict[str, Any]] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


def create_initial_state(company_input: Dict[str, Any]) -> WorkflowState:
    """Create initial workflow state from company input."""
    return {
        "company_input": company_input,
        "safety_check_passed": False,
        "validation_result": None,
        "validation_errors": [],
        "planner_iterations": 0,
        "max_planner_iterations": 3,
        "scraper_plan": None,
        "plan_approved": False,
        "plan_feedback": None,
        "search_terms": [],
        "search_query": {},
        "scraped_topics": [],
        "retrieval_errors": [],
        "analyzed_calls": [],
        "eligibility_results": [],
        "analysis_errors": [],
        "analysis_summary": None,
        "final_report": None,
        "report_format": "json",
        "current_step": "safety_check",
        "workflow_status": "running",
        "error_message": None,
        "start_time": datetime.now().isoformat(),
        "end_time": None,
    }


def get_state_summary(state: WorkflowState) -> Dict[str, Any]:
    """Get a human-readable summary of current state."""
    return {
        "status": state["workflow_status"],
        "current_step": state["current_step"],
        "planner_iterations": state["planner_iterations"],
        "topics_found": len(state["scraped_topics"]),
        "calls_analyzed": len(state["analyzed_calls"]),
        "errors": len(state["validation_errors"])
        + len(state["retrieval_errors"])
        + len(state["analysis_errors"]),
        "plan_approved": state["plan_approved"],
    }
