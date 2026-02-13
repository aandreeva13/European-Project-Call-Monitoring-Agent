"""
Master Agent - LangGraph Workflow for EU Call Finder.
Coordinates Safety Guard → Planner → Retrieval → Analysis → [Planner (loop) or Reporter]
"""

import os
import sys
from typing import Dict, Any, Literal
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Import state
from contracts.state import WorkflowState, create_initial_state

# Import implemented modules using importlib (for numbered folders)
import importlib.util


def _load_module(module_name: str, file_path: str):
    """Load a module from file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Load Safety Guard
_safety_module = _load_module(
    "safety",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "1_safety", "safety_guard.py"
    ),
)
_validator_module = _load_module(
    "validator",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "1_safety", "input_validator.py"
    ),
)
SafetyGuard = _safety_module.SafetyGuard
InputValidator = _validator_module.InputValidator

# Load Planner
_planner_module = _load_module(
    "planner",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "3_planning", "planner.py"
    ),
)
PlannerAgent = _planner_module.PlannerAgent

# Load Retrieval
_retrieval_module = _load_module(
    "scraper",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "4_retrieval", "scraper_manager.py"
    ),
)
scrape_topics_node = _retrieval_module.scrape_topics_node


# ==================== NODE IMPLEMENTATIONS ====================


def safety_check_node(state: WorkflowState) -> WorkflowState:
    """
    Node 1: Safety Check & Input Validation
    Validates user input for security threats and structural correctness.
    """
    print("\n" + "=" * 70)
    print("STEP 1: SAFETY CHECK & VALIDATION")
    print("=" * 70)

    company_input = state.get("company_input")
    if not company_input:
        return {
            **state,
            "safety_check_passed": False,
            "workflow_status": "failed",
            "error_message": "No company input provided",
            "current_step": "failed",
        }

    # Run safety guard
    try:
        guard = SafetyGuard()
        safety_result = guard.check(company_input)

        if not safety_result.is_valid:
            print(f"❌ Safety check failed: {safety_result.reason}")
            return {
                **state,
                "safety_check_passed": False,
                "validation_errors": [safety_result.reason],
                "workflow_status": "failed",
                "error_message": f"Safety check failed: {safety_result.reason}",
                "current_step": "failed",
            }

        print("✅ Safety check passed")

        # Run input validation
        validator = InputValidator()
        validation_result = validator.validate(company_input)

        if not validation_result.is_valid:
            print(f"❌ Validation failed: {validation_result.reason}")
            return {
                **state,
                "safety_check_passed": False,
                "validation_result": validation_result.__dict__,
                "validation_errors": [validation_result.reason],
                "workflow_status": "failed",
                "error_message": f"Validation failed: {validation_result.reason}",
                "current_step": "failed",
            }

        print(f"✅ Input validation passed (score: {validation_result.score}/10)")

        return {
            **state,
            "safety_check_passed": True,
            "validation_result": validation_result.__dict__,
            "current_step": "planning",
            "workflow_status": "running",
        }

    except Exception as e:
        print(f"❌ Safety check error: {str(e)}")
        return {
            **state,
            "safety_check_passed": False,
            "validation_errors": [str(e)],
            "workflow_status": "failed",
            "error_message": f"Safety check error: {str(e)}",
            "current_step": "failed",
        }


def planner_node(state: WorkflowState) -> WorkflowState:
    """
    Node 2: Planner
    Creates execution plan from company profile.
    Can be called multiple times (loop with analysis).
    """
    print("\n" + "=" * 70)
    print(f"STEP 2: PLANNING (Iteration {state.get('planner_iterations', 0) + 1})")
    print("=" * 70)

    company_input = state.get("company_input")

    # If we have feedback from critic, show it
    plan_feedback = state.get("plan_feedback")
    if plan_feedback:
        print(f"\n📋 Previous plan feedback: {plan_feedback}")

    try:
        planner = PlannerAgent()
        plan = planner.create_plan(company_input)

        print(f"\n✅ Plan created:")
        print(f"   Company: {plan['company_name']}")
        print(f"   Search queries: {len(plan['search_queries'])}")
        for i, query in enumerate(plan["search_queries"], 1):
            print(f"      {i}. {query}")
        print(f"   Target programs: {', '.join(plan['target_programs'])}")
        print(f"   Estimated calls: {plan['estimated_calls']}")

        # Extract search terms and query from plan
        search_terms = plan["search_queries"]
        search_query = plan["filter_config"]

        return {
            **state,
            "scraper_plan": plan,
            "search_terms": search_terms,
            "search_query": search_query,
            "planner_iterations": state.get("planner_iterations", 0) + 1,
            "current_step": "retrieval",
            "workflow_status": "running",
        }

    except Exception as e:
        print(f"❌ Planning error: {str(e)}")
        return {
            **state,
            "workflow_status": "failed",
            "error_message": f"Planning error: {str(e)}",
            "current_step": "failed",
        }


def retrieval_node(state: WorkflowState) -> WorkflowState:
    """
    Node 3: Retrieval / Web Scraping
    Executes the scraper with the planned search terms.
    """
    print("\n" + "=" * 70)
    print("STEP 3: RETRIEVAL / WEB SCRAPING")
    print("=" * 70)

    try:
        # Prepare state for scraper node
        scraper_state = {
            "search_terms": state.get("search_terms", []),
            "search_query": state.get("search_query", {}),
            "headless": True,  # Run headless in production
            "max_topics": 10,  # Limit for testing
        }

        print(f"\n🔍 Searching with terms: {scraper_state['search_terms']}")
        print(f"   Using EU Portal filters...")

        # Call scraper node
        result = scrape_topics_node(scraper_state)
        scraped_topics = result.get("scraped_topics", [])

        print(f"\n✅ Retrieved {len(scraped_topics)} topics")

        if scraped_topics:
            print(f"\n   First topic: {scraped_topics[0].get('title', 'N/A')[:60]}...")

        return {
            **state,
            "scraped_topics": scraped_topics,
            "current_step": "analysis",
            "workflow_status": "running",
        }

    except Exception as e:
        print(f"❌ Retrieval error: {str(e)}")
        return {
            **state,
            "retrieval_errors": [str(e)],
            "workflow_status": "failed",
            "error_message": f"Retrieval error: {str(e)}",
            "current_step": "failed",
        }


def analysis_node(state: WorkflowState) -> WorkflowState:
    """
    Node 4: Analysis (STUB - to be implemented)
    Analyzes scraped topics and decides whether to:
    - Loop back to planner (if results poor)
    - Continue to reporter (if results good)

    For now, this is a stub that makes a simple decision based on topic count.
    """
    print("\n" + "=" * 70)
    print("STEP 4: ANALYSIS")
    print("=" * 70)

    scraped_topics = state.get("scraped_topics", [])
    planner_iterations = state.get("planner_iterations", 0)
    max_iterations = state.get("max_planner_iterations", 3)

    print(f"\n📊 Analyzing {len(scraped_topics)} scraped topics...")

    # STUB: Simple decision logic
    # In real implementation, this would:
    # - Score each topic for relevance
    # - Check eligibility
    # - Use LLM critic to evaluate quality

    if len(scraped_topics) == 0:
        # No results - need to refine plan
        if planner_iterations < max_iterations:
            print(
                f"\n⚠️  No topics found. Refining plan (iteration {planner_iterations + 1}/{max_iterations})"
            )
            return {
                **state,
                "plan_approved": False,
                "plan_feedback": "No topics found with current search terms. Try broader keywords.",
                "current_step": "planning",  # Loop back to planner
                "workflow_status": "running",
            }
        else:
            print(
                f"\n⚠️  No topics found after {max_iterations} attempts. Continuing with empty results."
            )
            return {
                **state,
                "plan_approved": True,  # Force continue
                "analyzed_calls": [],
                "current_step": "reporting",
                "workflow_status": "running",
            }

    # We have results - approve plan
    print(f"\n✅ Analysis complete. Found {len(scraped_topics)} relevant calls.")
    print("   Plan approved. Proceeding to reporting...")

    # STUB: Convert topics to analyzed calls format
    analyzed_calls = []
    for topic in scraped_topics:
        analyzed_calls.append(
            {
                "id": topic.get("id"),
                "title": topic.get("title"),
                "url": topic.get("url"),
                "status": topic.get("status"),
                "programme": topic.get("general_info", {}).get("programme", "Unknown"),
                "relevance_score": 7.0,  # STUB score
                "eligibility_passed": True,  # STUB
                "summary": topic.get("content", {}).get("description", "")[:200]
                + "...",
                "deadline": topic.get("general_info", {})
                .get("dates", {})
                .get("deadline", "N/A"),
            }
        )

    return {
        **state,
        "plan_approved": True,
        "analyzed_calls": analyzed_calls,
        "current_step": "reporting",
        "workflow_status": "running",
    }


def reporter_node(state: WorkflowState) -> WorkflowState:
    """
    Node 5: Reporter (STUB - to be implemented)
    Generates final report from analyzed calls.
    """
    print("\n" + "=" * 70)
    print("STEP 5: REPORTING")
    print("=" * 70)

    analyzed_calls = state.get("analyzed_calls", [])
    company_input = state.get("company_input", {})

    print(f"\n📝 Generating report for {len(analyzed_calls)} calls...")

    # STUB: Simple report generation
    report = {
        "company_name": company_input.get("company", {}).get("name", "Unknown"),
        "search_date": datetime.now().isoformat(),
        "total_calls_found": len(analyzed_calls),
        "calls": analyzed_calls,
        "summary": f"Found {len(analyzed_calls)} relevant EU funding calls matching your profile.",
        "recommendations": [
            "Review each call for eligibility requirements",
            "Check deadlines carefully",
            "Prepare consortium partners if needed",
        ]
        if analyzed_calls
        else ["No matching calls found. Try broadening your search criteria."],
    }

    print(f"\n✅ Report generated!")
    print(f"   Total calls: {report['total_calls_found']}")
    print(f"   Summary: {report['summary']}")

    return {
        **state,
        "final_report": report,
        "workflow_status": "completed",
        "current_step": END,
        "end_time": datetime.now().isoformat(),
    }


# ==================== CONDITIONAL EDGES ====================


def should_continue_after_safety(state: WorkflowState) -> Literal["planner", "failed"]:
    """Decide whether to continue to planner or fail after safety check."""
    if state.get("safety_check_passed"):
        return "planner"
    return "failed"


def should_continue_after_analysis(
    state: WorkflowState,
) -> Literal["planner", "reporter"]:
    """
    Decide whether to loop back to planner or continue to reporter.
    This creates the Planner ↔ Analysis loop.
    """
    if state.get("plan_approved"):
        return "reporter"
    return "planner"  # Loop back for refinement


# ==================== WORKFLOW CONSTRUCTION ====================


def create_workflow() -> StateGraph:
    """Create and configure the LangGraph workflow."""

    # Initialize the graph with our state type
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("safety_check", safety_check_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("reporter", reporter_node)

    # Set entry point
    workflow.set_entry_point("safety_check")

    # Add edges with conditional routing
    workflow.add_conditional_edges(
        "safety_check",
        should_continue_after_safety,
        {"planner": "planner", "failed": END},
    )

    # Sequential flow: planner → retrieval → analysis
    workflow.add_edge("planner", "retrieval")
    workflow.add_edge("retrieval", "analysis")

    # Conditional edge: analysis → (planner [loop] or reporter)
    workflow.add_conditional_edges(
        "analysis",
        should_continue_after_analysis,
        {
            "planner": "planner",  # LOOP: Refine plan
            "reporter": "reporter",  # CONTINUE: Generate report
        },
    )

    # End after reporting
    workflow.add_edge("reporter", END)

    return workflow


def compile_workflow(checkpointer=None):
    """Compile the workflow with optional checkpointing."""
    workflow = create_workflow()

    if checkpointer is None:
        checkpointer = MemorySaver()

    app = workflow.compile(checkpointer=checkpointer)
    return app


# ==================== EXECUTION FUNCTIONS ====================


def run_workflow(
    company_input: Dict[str, Any], thread_id: str = None
) -> Dict[str, Any]:
    """
    Run the complete workflow for a company.

    Args:
        company_input: Company profile data
        thread_id: Optional thread ID for persistence

    Returns:
        Final workflow state with results
    """
    # Create initial state
    initial_state = create_initial_state(company_input)

    # Compile workflow
    app = compile_workflow()

    # Configure thread
    config = {"configurable": {"thread_id": thread_id or "default"}}

    # Run workflow
    print("\n" + "🚀" * 35)
    print("STARTING EU CALL FINDER WORKFLOW")
    print("🚀" * 35)

    for event in app.stream(initial_state, config):
        # Events are streamed as nodes complete
        pass

    # Get final state
    final_state = app.get_state(config)

    print("\n" + "=" * 70)
    print("WORKFLOW COMPLETED")
    print("=" * 70)
    print(f"Status: {final_state.values.get('workflow_status')}")
    print(f"Total calls found: {len(final_state.values.get('analyzed_calls', []))}")

    if final_state.values.get("error_message"):
        print(f"Error: {final_state.values['error_message']}")

    return final_state.values


def get_workflow_graph():
    """Get the workflow graph structure for visualization."""
    workflow = create_workflow()
    return workflow


# ==================== MAIN ====================

if __name__ == "__main__":
    # Test the workflow
    from contracts.schemas import CompanyInput, CompanyProfile, Domain, DomainLevel

    # Create test company
    test_company = CompanyInput(
        company=CompanyProfile(
            name="AI Startup Bulgaria",
            description="We develop artificial intelligence solutions for healthcare diagnostics using computer vision and deep learning.",
            type="SME",
            employees=25,
            country="Bulgaria",
            domains=[
                Domain(
                    name="Artificial Intelligence",
                    sub_domains=["Computer Vision", "Deep Learning"],
                    level=DomainLevel.ADVANCED,
                )
            ],
        )
    )

    # Run workflow
    result = run_workflow(test_company.model_dump())

    # Print final report
    if result.get("final_report"):
        print("\n" + "=" * 70)
        print("FINAL REPORT")
        print("=" * 70)
        import json

        print(json.dumps(result["final_report"], indent=2, default=str))
