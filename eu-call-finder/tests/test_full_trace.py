#!/usr/bin/env python3
"""
Complete workflow trace showing ALL data exchanges between nodes.
This demonstrates the loop with full visibility of what each node receives and sends.
"""

import sys
import os
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

import importlib.util

print("=" * 90)
print("EU CALL FINDER - COMPLETE WORKFLOW TRACE")
print("Showing all data exchanges between nodes")
print("=" * 90)

print("\n[SYSTEM] Loading modules...")

# Load all modules
spec = importlib.util.spec_from_file_location("contracts", "contracts/schemas.py")
contracts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contracts)

spec2 = importlib.util.spec_from_file_location("state", "contracts/state.py")
state_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(state_module)

spec3 = importlib.util.spec_from_file_location(
    "master_agent", "2_orchestration/master_agent.py"
)
master = importlib.util.module_from_spec(spec3)
spec3.loader.exec_module(master)

spec4 = importlib.util.spec_from_file_location(
    "scraper_manager", "4_retrieval/scraper_manager.py"
)
scraper_module = importlib.util.module_from_spec(spec4)
spec4.loader.exec_module(scraper_module)

print("[SYSTEM] All modules loaded successfully!")

# Import functions
CompanyInput = contracts.CompanyInput
CompanyProfile = contracts.CompanyProfile
Domain = contracts.Domain
DomainLevel = contracts.DomainLevel
create_initial_state = state_module.create_initial_state

safety_check_node = master.safety_check_node
planner_node = master.planner_node
analysis_node = master.analysis_node
reporter_node = master.reporter_node
scrape_topics_node = scraper_module.scrape_topics_node


def print_state_summary(state, label="STATE"):
    """Print a summary of current state"""
    print(f"\n{'=' * 90}")
    print(f"{label} SUMMARY")
    print(f"{'=' * 90}")
    print(f"  Current Step: {state.get('current_step', 'N/A')}")
    print(f"  Workflow Status: {state.get('workflow_status', 'N/A')}")
    print(f"  Planner Iterations: {state.get('planner_iterations', 0)}")
    print(f"  Safety Check Passed: {state.get('safety_check_passed', False)}")
    print(f"  Plan Approved: {state.get('plan_approved', 'N/A')}")
    print(f"  Topics Count: {len(state.get('scraped_topics', []))}")
    print(f"  Analyzed Calls: {len(state.get('analyzed_calls', []))}")
    if state.get("plan_feedback"):
        print(f"  Plan Feedback: {state['plan_feedback'][:80]}...")


def print_full_workflow():
    """Execute complete workflow with full tracing"""

    # STEP 0: Setup
    print("\n" + "=" * 90)
    print("STEP 0: INITIALIZATION - Creating Company Profile")
    print("=" * 90)

    company_input = CompanyInput(
        company=CompanyProfile(
            name="HealthAI Bulgaria",
            description="Bulgarian company developing AI-powered diagnostic tools for early disease detection. We specialize in machine learning for medical imaging and predictive analytics for patient care.",
            type="SME",
            employees=30,
            country="Bulgaria",
            city="Sofia",
            domains=[
                Domain(
                    name="Artificial Intelligence",
                    sub_domains=[
                        "Machine Learning",
                        "Medical Imaging",
                        "Predictive Analytics",
                    ],
                    level=DomainLevel.ADVANCED,
                ),
                Domain(
                    name="Healthcare Technology",
                    sub_domains=["Diagnostic Tools", "Patient Care"],
                    level=DomainLevel.EXPERT,
                ),
            ],
        )
    )

    print("\n[INPUT DATA - Company Profile]:")
    print(f"  Name: {company_input.company.name}")
    print(f"  Type: {company_input.company.type}")
    print(f"  Country: {company_input.company.country}")
    print(f"  Employees: {company_input.company.employees}")
    print(f"  Description: {company_input.company.description[:80]}...")
    print(f"\n  Domains:")
    for d in company_input.company.domains:
        print(f"    - {d.name} ({d.level.value})")
        print(f"      Sub-domains: {', '.join(d.sub_domains)}")

    # Create initial state
    state = create_initial_state(company_input.model_dump())

    print("\n[INITIAL STATE CREATED]:")
    print(f"  State Type: {type(state)}")
    print(f"  Keys: {list(state.keys())[:10]}")
    print_state_summary(state, "INITIAL STATE")

    # STEP 1: Safety Check
    print("\n" + "=" * 90)
    print("STEP 1: SAFETY CHECK NODE")
    print("=" * 90)
    print("\n[RECEIVING]:")
    print(f"  Input: state with company profile")
    print(f"  Company Name: {state['company_input']['company']['name']}")

    state = safety_check_node(state)

    print("\n[SENDING]:")
    print(f"  Output: Updated state")
    print(f"  safety_check_passed: {state['safety_check_passed']}")
    if state.get("validation_result"):
        print(
            f"  Validation Score: {state['validation_result'].get('score', 'N/A')}/10"
        )
    print_state_summary(state, "AFTER SAFETY CHECK")

    iteration = 0
    max_iterations = 3  # Run up to 3 iterations to show the loop

    while iteration < max_iterations:
        iteration += 1

        print("\n" + "=" * 90)
        print(f"ITERATION {iteration} (Max: {max_iterations})")
        print("=" * 90)

        # STEP 2: Planner
        print(f"\n{'=' * 90}")
        print(f"STEP 2.{iteration}: PLANNER NODE")
        print(f"{'=' * 90}")
        print("\n[RECEIVING]:")
        print(f"  Input: state with company profile")
        print(f"  Company Input Keys: {list(state['company_input'].keys())}")

        if state.get("plan_feedback"):
            print(f"\n  *** FEEDBACK FROM PREVIOUS ANALYSIS ***")
            print(f"  Feedback: {state['plan_feedback']}")
            print(f"  *** USING FEEDBACK TO REFINE PLAN ***")
        else:
            print(f"\n  No feedback (first iteration)")

        # Show what the planner receives
        company_data = state["company_input"]["company"]
        print(f"\n  Company Data Received:")
        print(f"    - Name: {company_data['name']}")
        print(f"    - Type: {company_data['type']}")
        print(f"    - Domains: {[d['name'] for d in company_data['domains']]}")

        state = planner_node(state)

        print("\n[SENDING]:")
        print(f"  Output: Updated state with plan")
        plan = state.get("scraper_plan", {})
        print(f"\n  Generated Plan:")
        print(f"    Company: {plan.get('company_name')}")
        print(f"    Search Queries ({len(plan.get('search_queries', []))}):")
        for i, q in enumerate(plan.get("search_queries", []), 1):
            print(f"      {i}. {q}")
        print(f"    Target Programs: {', '.join(plan.get('target_programs', []))}")
        print(f"    Estimated Calls: {plan.get('estimated_calls')}")
        print(f"    Reasoning: {plan.get('reasoning', 'N/A')}")
        print(f"\n  Search Terms: {state.get('search_terms', [])}")

        print_state_summary(state, f"AFTER PLANNER (Iteration {iteration})")

        # STEP 3: Retrieval
        print(f"\n{'=' * 90}")
        print(f"STEP 3.{iteration}: RETRIEVAL NODE (API-Only)")
        print(f"{'=' * 90}")
        print("\n[RECEIVING]:")
        print(f"  Input: state with search terms and query")
        print(f"  Search Terms: {state.get('search_terms', [])}")

        state = scrape_topics_node(state)

        print("\n[SENDING]:")
        print(f"  Output: Updated state with scraped topics")
        topics = state.get("scraped_topics", [])
        print(f"  Topics Found: {len(topics)}")
        if topics:
            print(f"\n  Sample Topics:")
            for i, t in enumerate(topics[:5], 1):
                print(f"    {i}. {t.get('id', 'N/A')}: {t.get('title', 'N/A')[:60]}...")

        print_state_summary(state, f"AFTER RETRIEVAL (Iteration {iteration})")

        # STEP 4: Analysis
        print(f"\n{'=' * 90}")
        print(f"STEP 4.{iteration}: ANALYSIS NODE")
        print(f"{'=' * 90}")
        print("\n[RECEIVING]:")
        print(
            f"  Input: state with {len(state.get('scraped_topics', []))} scraped topics"
        )
        print(f"  Company Profile: {state['company_input']['company']['name']}")
        print(f"  Current Iteration: {state.get('planner_iterations', 0)}")

        state = analysis_node(state)

        print("\n[SENDING]:")
        print(f"  Output: Updated state with analysis results")

        analyzed = state.get("analyzed_calls", [])
        print(f"\n  Analysis Results:")
        print(f"    Calls Analyzed: {len(analyzed)}")

        summary = state.get("analysis_summary", {})
        print(f"\n  Decision Summary:")
        print(f"    Decision: {summary.get('decision', 'N/A').upper()}")
        print(f"    High Scores (8+): {summary.get('stats', {}).get('high_scores', 0)}")
        print(
            f"    Average Score: {summary.get('stats', {}).get('average_score', 0)}/10"
        )
        print(f"    Reasoning: {summary.get('reasoning', 'N/A')[:80]}...")
        print(f"\n  Plan Approved: {state.get('plan_approved')}")

        if state.get("plan_feedback"):
            print(f"\n  *** FEEDBACK GENERATED FOR NEXT ITERATION ***")
            print(f"  Feedback: {state['plan_feedback'][:100]}...")

        print_state_summary(state, f"AFTER ANALYSIS (Iteration {iteration})")

        # Check if we should continue or loop
        if state.get("plan_approved"):
            print(f"\n[DECISION] Plan approved! Exiting loop.")
            print(f"  Found {len(analyzed)} good calls. Proceeding to reporter.")
            break
        elif iteration >= max_iterations:
            print(f"\n[DECISION] Max iterations ({max_iterations}) reached.")
            print(f"  Proceeding to reporter with current results.")
            break
        else:
            print(f"\n[DECISION] Plan NOT approved. Looping back to planner...")
            print(f"  Will run Iteration {iteration + 1} with feedback...")
            print(f"\n  >>>>> LOOPING BACK TO PLANNER <<<<<")

    # STEP 5: Reporter
    print("\n" + "=" * 90)
    print("STEP 5: REPORTER NODE")
    print("=" * 90)
    print("\n[RECEIVING]:")
    print(f"  Input: state with {len(state.get('analyzed_calls', []))} analyzed calls")
    print(f"  Company: {state['company_input']['company']['name']}")

    state = reporter_node(state)

    print("\n[SENDING]:")
    print(f"  Output: Final report")
    report = state.get("final_report", {})
    print(f"\n  Final Report:")
    print(f"    Company: {report.get('company_name')}")
    print(f"    Total Calls: {report.get('total_calls_found')}")
    print(f"    Summary: {report.get('summary')}")
    if report.get("calls"):
        print(f"\n    Top Recommendations:")
        for i, call in enumerate(report["calls"][:5], 1):
            rec = call.get("recommendation", {})
            print(f"      {i}. {call.get('title', 'N/A')[:45]}...")
            print(f"         Action: {rec.get('label', 'N/A')}")

    print_state_summary(state, "FINAL STATE")

    # FINAL SUMMARY
    print("\n" + "=" * 90)
    print("WORKFLOW COMPLETE - FINAL SUMMARY")
    print("=" * 90)
    print(f"\nExecution Summary:")
    print(f"  Total Planner Iterations: {state.get('planner_iterations', 0)}")
    print(f"  Topics Retrieved: {len(state.get('scraped_topics', []))}")
    print(f"  Calls Analyzed: {len(state.get('analyzed_calls', []))}")
    print(f"  Final Status: {state.get('workflow_status')}")
    print(f"  Report Generated: {state.get('final_report') is not None}")

    print("\n" + "=" * 90)
    print("TRACE COMPLETE")
    print("=" * 90)


if __name__ == "__main__":
    try:
        print_full_workflow()
    except KeyboardInterrupt:
        print("\n\n[SYSTEM] Interrupted by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback

        traceback.print_exc()
