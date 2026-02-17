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

# Load Smart Planner
_smart_planner_module = _load_module(
    "smart_planner",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "3_planning", "smart_planner.py"
    ),
)
SmartPlanner = _smart_planner_module.SmartPlanner
create_smart_plan = _smart_planner_module.create_smart_plan

# Load Retrieval
_retrieval_module = _load_module(
    "scraper",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "4_retrieval", "scraper_manager.py"
    ),
)
scrape_topics_node = _retrieval_module.scrape_topics_node

# Load Analysis Modules
_analysis_scorer = _load_module(
    "scorer",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "5_analysis", "scorer.py"),
)
score_call = _analysis_scorer.score_call

_analysis_eligibility = _load_module(
    "eligibility",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "5_analysis", "eligibility.py"
    ),
)
apply_eligibility_filters = _analysis_eligibility.apply_eligibility_filters

_analysis_critic = _load_module(
    "llm_critic",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "5_analysis", "llm_critic.py"
    ),
)
perform_qualitative_analysis = _analysis_critic.perform_qualitative_analysis

_analysis_reflection = _load_module(
    "reflection",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "5_analysis", "reflection.py"
    ),
)
reflect_on_results = _analysis_reflection.reflect_on_results

# Load Reporter Module
_reporter_module = _load_module(
    "reporter",
    os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "6_reporter", "reporter.py"
    ),
)
generate_comprehensive_report = _reporter_module.generate_comprehensive_report


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
        guard = SafetyGuard(use_llm=False)  # Use regex-only mode to avoid LLM delays

        # Check if company_input is dict or CompanyInput object
        if isinstance(company_input, dict):
            # For dict input, extract text manually for safety check
            text_parts = []
            company = company_input.get("company", {})
            text_parts.append(company.get("name", ""))
            text_parts.append(company.get("description", ""))
            text_parts.append(company.get("country", ""))
            text_parts.append(company.get("city", ""))
            for domain in company.get("domains", []):
                text_parts.append(domain.get("name", ""))
                text_parts.extend(domain.get("sub_domains", []))

            # Simple regex-based safety check on text
            import re

            # Filter out None values and convert to string
            text_parts = [str(part) for part in text_parts if part is not None]
            text = " ".join(text_parts).lower()

            # Check for suspicious patterns
            suspicious_patterns = [
                r"<script",
                r"javascript:",
                r"on\w+\s*=",
                r"ignore\s+previous",
                r"override\s+instructions",
                r"system\s*prompt:",
                r"jailbreak",
                r"DAN\s+mode",
            ]

            threats_found = []
            for pattern in suspicious_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    threats_found.append(pattern)

            if threats_found:
                print(f"[FAIL] Safety check failed: Suspicious patterns detected")
                return {
                    **state,
                    "safety_check_passed": False,
                    "validation_errors": [
                        f"Security threats detected: {threats_found}"
                    ],
                    "workflow_status": "failed",
                    "error_message": "Safety check failed: Security threats detected",
                    "current_step": "failed",
                }

            safety_result = type(
                "obj",
                (object,),
                {
                    "is_valid": True,
                    "score": 10.0,
                    "reason": "Basic safety check passed",
                },
            )()
        else:
            # It's a CompanyInput object
            safety_result = guard.check(company_input)

        if not safety_result.is_valid:
            print(f"[FAIL] Safety check failed: {safety_result.reason}")
            return {
                **state,
                "safety_check_passed": False,
                "validation_errors": [safety_result.reason],
                "workflow_status": "failed",
                "error_message": f"Safety check failed: {safety_result.reason}",
                "current_step": "failed",
            }

        print("[OK] Safety check passed")

        # Run input validation
        if isinstance(company_input, dict):
            # For dict input, create a basic validation result
            company = company_input.get("company", {})
            has_name = bool(company.get("name"))
            has_description = len(company.get("description", "")) >= 20
            has_domains = len(company.get("domains", [])) > 0

            validation_passed = has_name and has_description and has_domains
            validation_score = 7.0 if validation_passed else 5.0

            validation_result = type(
                "obj",
                (object,),
                {
                    "is_valid": validation_passed,
                    "score": validation_score,
                    "reason": "Basic validation passed"
                    if validation_passed
                    else "Missing required fields",
                    "missing_fields": [],
                },
            )()
        else:
            # It's a CompanyInput object - run full validation
            validator = InputValidator()
            validation_result = validator.validate(company_input)

        if not validation_result.is_valid:
            print(f"[FAIL] Validation failed: {validation_result.reason}")
            return {
                **state,
                "safety_check_passed": False,
                "validation_result": validation_result.__dict__,
                "validation_errors": [validation_result.reason],
                "workflow_status": "failed",
                "error_message": f"Validation failed: {validation_result.reason}",
                "current_step": "failed",
            }

        print(f"[OK] Input validation passed (score: {validation_result.score}/10)")

        return {
            **state,
            "safety_check_passed": True,
            "validation_result": validation_result.__dict__,
            "current_step": "planning",
            "workflow_status": "running",
        }

    except Exception as e:
        print(f"[FAIL] Safety check error: {str(e)}")
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
    plan_feedback = state.get("plan_feedback")

    try:
        # Use Smart Planner for better analysis
        print("\n[ANALYSIS] Deep analyzing company profile...")
        planner = SmartPlanner()

        # Ensure company_input is dict format
        if not isinstance(company_input, dict):
            company_input = company_input.model_dump()

        # Create smart plan with feedback if available
        if plan_feedback:
            print(f"\n[REFINEMENT] Using feedback from previous iteration:")
            print(f"   {plan_feedback[:100]}...")

        plan = create_smart_plan(company_input, previous_feedback=plan_feedback)

        # Display analysis results
        analysis = plan.get("analysis", {})
        print(f"\n[ANALYSIS RESULTS]:")
        print(
            f"   Technologies Detected: {', '.join(analysis.get('technologies', []))}"
        )
        print(f"   Applications: {', '.join(analysis.get('applications', []))}")
        print(f"   Focus Areas: {', '.join(analysis.get('focus_areas', [])[:3])}")
        print(f"   Target EU Programs: {', '.join(plan.get('target_programs', []))}")

        print(f"\n[OK] Smart Plan Created:")
        print(f"   Company: {plan['company_name']}")
        print(f"   Search Queries ({len(plan['search_queries'])}):")
        for i, query in enumerate(plan["search_queries"], 1):
            print(f"      {i}. {query}")
        print(f"   Target Programs: {', '.join(plan['target_programs'])}")
        print(f"   Estimated Calls: {plan['estimated_calls']}")
        print(f"   Reasoning: {plan['reasoning']}")

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
        print(f"[FAIL] Planning error: {str(e)}")
        import traceback

        traceback.print_exc()
        return {
            **state,
            "workflow_status": "failed",
            "error_message": f"Planning error: {str(e)}",
            "current_step": "failed",
        }

        print(f"\n[OK] Plan created:")
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
        print(f"[FAIL] Planning error: {str(e)}")
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
            "max_topics": 2,  # Limit for testing - will be removed later
        }

        print(f"\n[SEARCH] Searching with terms: {scraper_state['search_terms']}")
        print(f"   Using EU Portal filters...")

        # Call scraper node
        result = scrape_topics_node(scraper_state)
        scraped_topics = result.get("scraped_topics", [])

        print(f"\n[OK] Retrieved {len(scraped_topics)} topics")

        if scraped_topics:
            print(f"\n   First topic: {scraped_topics[0].get('title', 'N/A')[:60]}...")

        return {
            **state,
            "scraped_topics": scraped_topics,
            "current_step": "analysis",
            "workflow_status": "running",
        }

    except Exception as e:
        print(f"[FAIL] Retrieval error: {str(e)}")
        return {
            **state,
            "retrieval_errors": [str(e)],
            "workflow_status": "failed",
            "error_message": f"Retrieval error: {str(e)}",
            "current_step": "failed",
        }


def analysis_node(state: WorkflowState) -> WorkflowState:
    """
    Node 4: Analysis
    Analyzes scraped topics using real analysis modules:
    - Scorer: Calculates weighted relevance scores
    - Eligibility: Checks hard constraints (country, type, budget, etc.)
    - LLM Critic: Provides qualitative analysis
    - Reflection: Decides whether to loop back or continue
    """
    print("\n" + "=" * 70)
    print("STEP 4: ANALYSIS")
    print("=" * 70)

    scraped_topics = state.get("scraped_topics", [])
    company_input = state.get("company_input", {})
    planner_iterations = state.get("planner_iterations", 0)
    max_iterations = state.get("max_planner_iterations", 3)

    print(f"\n[STATS] Analyzing {len(scraped_topics)} scraped topics...")

    if len(scraped_topics) == 0:
        # No results - need to refine plan
        if planner_iterations < max_iterations:
            print(
                f"\n[WARN]  No topics found. Refining plan (iteration {planner_iterations + 1}/{max_iterations})"
            )
            return {
                **state,
                "plan_approved": False,
                "plan_feedback": "No topics found with current search terms. Try broader keywords.",
                "current_step": "planning",
                "workflow_status": "running",
            }
        else:
            print(
                f"\n[WARN]  No topics found after {max_iterations} attempts. Continuing with empty results."
            )
            return {
                **state,
                "plan_approved": True,
                "analyzed_calls": [],
                "current_step": "reporting",
                "workflow_status": "running",
            }

    # Extract company profile for analysis
    company_profile = company_input.get("company", {})
    analyzed_calls = []

    print(f"\n[SEARCH] Running detailed analysis on {len(scraped_topics)} calls...")

    for i, topic in enumerate(scraped_topics, 1):
        print(
            f"\n  [{i}/{len(scraped_topics)}] Analyzing: {topic.get('title', 'N/A')[:50]}..."
        )

        # Step 1: Check eligibility (hard constraints)
        eligibility = apply_eligibility_filters(topic, company_profile)
        print(f"      Eligibility: {'PASS' if eligibility['all_passed'] else 'FAIL'}")

        # Step 2: Get qualitative analysis from LLM Critic
        try:
            qualitative = perform_qualitative_analysis(topic, company_profile)
            print(
                f"      Qualitative: {qualitative.get('match_summary', 'N/A')[:60]}..."
            )
        except Exception as e:
            print(f"      Qualitative: Error - {str(e)[:50]}")
            qualitative = {
                "match_summary": "Analysis unavailable",
                "domain_matches": [],
                "keyword_hits": [],
                "analysis_method": "error",
            }

        # Step 3: Calculate weighted score
        try:
            scoring = score_call(topic, company_profile, qualitative)
            print(
                f"      Score: {scoring['total']}/10 ({scoring['recommendation']['label']})"
            )
        except Exception as e:
            print(f"      Score: Error - {str(e)[:50]}")
            scoring = {
                "total": 5.0,
                "domain_match": 5.0,
                "keyword_match": 5.0,
                "eligibility_fit": 5.0,
                "budget_feasibility": 5.0,
                "strategic_value": 5.0,
                "deadline_comfort": 5.0,
                "recommendation": {
                    "action": "consider",
                    "label": "ОБМИСЛЕТЕ",
                    "color": "yellow",
                },
            }

        # Build analyzed call record
        analyzed_call = {
            "id": topic.get("id"),
            "title": topic.get("title"),
            "url": topic.get("url"),
            "status": topic.get("status"),
            "programme": topic.get("general_info", {}).get("programme", "Unknown"),
            "relevance_score": scoring["total"],
            "eligibility_passed": eligibility["all_passed"],
            "eligibility_details": eligibility,
            "score_breakdown": {
                "domain_match": scoring["domain_match"],
                "keyword_match": scoring["keyword_match"],
                "eligibility_fit": scoring["eligibility_fit"],
                "budget_feasibility": scoring["budget_feasibility"],
                "strategic_value": scoring["strategic_value"],
                "deadline_comfort": scoring["deadline_comfort"],
            },
            "recommendation": scoring["recommendation"],
            "match_summary": qualitative.get("match_summary", ""),
            "domain_matches": qualitative.get("domain_matches", []),
            "keyword_hits": qualitative.get("keyword_hits", []),
            "suggested_partners": qualitative.get("suggested_partners", []),
            "estimated_effort": qualitative.get("estimated_effort_hours", "80-150"),
            "deadline": topic.get("general_info", {})
            .get("dates", {})
            .get("deadline", "N/A"),
            "budget": topic.get("general_info", {}).get("budget", "N/A"),
            "analysis_method": qualitative.get("analysis_method", "rule_based"),
        }

        analyzed_calls.append(analyzed_call)

    # Step 4: Use reflection to decide next action
    print(f"\n[THINK] Evaluating results and deciding next step...")

    search_params = {
        "max_results": 30,
        "portals": ["ftop", "eufunds_bg"],
    }

    reflection = reflect_on_results(analyzed_calls, search_params, planner_iterations)

    print(f"\n[CHART] Analysis Summary:")
    print(f"   Total analyzed: {len(analyzed_calls)}")
    print(f"   High scores (8+): {reflection['stats']['high_scores']}")
    print(f"   Medium scores (6-8): {reflection['stats']['medium_scores']}")
    print(f"   Average score: {reflection['stats']['average_score']}/10")
    print(f"   Decision: {reflection['decision'].upper()}")
    print(f"   Reasoning: {reflection['reasoning']}")

    # Decide whether to loop or continue
    if reflection["decision"] == "finalize" or planner_iterations >= max_iterations:
        print(f"\n[OK] Analysis complete. Proceeding to reporting...")
        return {
            **state,
            "analyzed_calls": analyzed_calls,
            "plan_approved": True,
            "current_step": "reporting",
            "workflow_status": "running",
            "analysis_summary": reflection,
        }
    elif reflection["decision"] == "refine":
        print(f"\n[WARN] Results need refinement. Looping back to planner...")
        recommendations = "; ".join(reflection["recommendations"])
        return {
            **state,
            "analyzed_calls": analyzed_calls,
            "plan_approved": False,
            "plan_feedback": f"Results need refinement: {recommendations}",
            "current_step": "planning",
            "workflow_status": "running",
            "analysis_summary": reflection,
        }
    else:
        # expand or other decisions - continue with what we have
        print(f"\n[OK] Continuing with current results...")
        return {
            **state,
            "analyzed_calls": analyzed_calls,
            "plan_approved": True,
            "current_step": "reporting",
            "workflow_status": "running",
            "analysis_summary": reflection,
        }


def reporter_node(state: WorkflowState) -> WorkflowState:
    """
    Node 5: Reporter
    Generates comprehensive LLM-powered report with card-based structure.
    """
    print("\n" + "=" * 70)
    print("STEP 5: REPORTING")
    print("=" * 70)

    analyzed_calls = state.get("analyzed_calls", [])
    company_input = state.get("company_input", {})

    print(
        f"\n[REPORT] Generating comprehensive report for {len(analyzed_calls)} calls..."
    )

    try:
        # Use the LLM-powered reporter module
        print("[REPORT] Calling generate_comprehensive_report...")
        report = generate_comprehensive_report(analyzed_calls, company_input)

        print(f"\n[OK] LLM Report generated!")
        print(f"   Report type: {report.get('report_type', 'unknown')}")
        print(f"   Total calls: {report.get('total_calls', 0)}")
        print(f"   Funding cards: {len(report.get('funding_cards', []))}")

        # Debug: Print first card details
        if report.get("funding_cards"):
            first_card = report["funding_cards"][0]
            print(f"\n[DEBUG] First card details:")
            print(f"   Title: {first_card.get('title', 'N/A')}")
            print(
                f"   Short summary: {first_card.get('short_summary', 'N/A')[:100]}..."
            )
            print(
                f"   Why recommended: {first_card.get('why_recommended', 'N/A')[:100]}..."
            )

        # Save full report to JSON for debugging
        import json

        debug_file = f"final_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(debug_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n[REPORT] Full report saved to: {debug_file}")

    except Exception as e:
        print(f"\n[ERROR] LLM report failed: {e}")
        import traceback

        traceback.print_exc()
        print("[REPORT] Falling back to basic report generation...")

        # Fallback to basic report generation inline
        company = (
            company_input.get("company", {}) if isinstance(company_input, dict) else {}
        )

        # Build funding cards from analyzed calls
        funding_cards = []
        for call in analyzed_calls:
            relevance = call.get("relevance_score", 0)
            match_pct = int(relevance * 10)

            card = {
                "id": call.get("id", ""),
                "title": call.get("title", "Untitled"),
                "programme": call.get("programme", ""),
                "description": call.get("raw_data", {}).get("description", "")[:500]
                if call.get("raw_data")
                else call.get("description", ""),
                "short_summary": call.get("match_summary", ""),
                "match_percentage": match_pct,
                "relevance_score": relevance,
                "eligibility_passed": call.get("eligibility_passed", False),
                "budget": call.get("budget", "N/A"),
                "deadline": call.get("deadline", "N/A"),
                "url": call.get("url", ""),
                "status": call.get("status", ""),
                "tags": call.get("keyword_hits", []),
                "why_recommended": call.get("match_summary", "")[:150]
                if call.get("match_summary")
                else f"Match score: {relevance}/10",
                "key_benefits": [f"Relevance score: {relevance}/10"]
                if relevance > 0
                else [],
                "action_items": [
                    "Review full call details",
                    "Check eligibility requirements",
                    f"Note deadline: {call.get('deadline', 'TBD')}",
                ],
                "success_probability": "high"
                if match_pct >= 80
                else "medium"
                if match_pct >= 60
                else "low",
                "domain_matches": call.get("domain_matches", []),
                "suggested_partners": call.get("suggested_partners", []),
            }
            funding_cards.append(card)

        # Sort by match percentage
        funding_cards.sort(key=lambda x: x["match_percentage"], reverse=True)

        # Count priorities
        high_priority = len([c for c in funding_cards if c["match_percentage"] >= 80])
        medium_priority = len(
            [c for c in funding_cards if 60 <= c["match_percentage"] < 80]
        )
        low_priority = len([c for c in funding_cards if c["match_percentage"] < 60])

        # Build fallback report
        report = {
            "company_profile": {
                "name": company.get("name", "Unknown"),
                "type": company.get("type", ""),
                "country": company.get("country", ""),
                "employees": company.get("employees", 0),
                "description": company.get("description", ""),
                "domains": company.get("domains", []),
            },
            "company_summary": {
                "profile_overview": f"{company.get('name', 'Company')} is a {company.get('type', 'organization')} based in {company.get('country', 'EU')}.",
                "key_strengths": [
                    d.get("name", "")
                    for d in company.get("domains", [])
                    if d.get("name")
                ],
                "recommended_focus_areas": [],
            },
            "overall_assessment": {
                "total_opportunities": len(analyzed_calls),
                "high_priority_count": high_priority,
                "medium_priority_count": medium_priority,
                "low_priority_count": low_priority,
                "summary_text": f"Found {len(analyzed_calls)} relevant EU funding calls matching your profile.",
                "strategic_advice": "Focus on high-priority opportunities (80%+ match) first.",
            },
            "funding_cards": funding_cards,
            "top_recommendations": [
                {
                    "call_id": c["id"],
                    "priority_rank": i + 1,
                    "match_percentage": c["match_percentage"],
                    "why_recommended": c["why_recommended"][:100],
                    "success_probability": c["success_probability"],
                }
                for i, c in enumerate(funding_cards[:3])
            ],
            "total_calls": len(analyzed_calls),
            "report_type": "fallback",
            "generated_at": datetime.now().isoformat(),
        }

        print(f"\n[OK] Fallback report generated!")

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
    print("\n" + "=" * 70)
    print("STARTING EU CALL FINDER WORKFLOW")
    print("=" * 70)

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
