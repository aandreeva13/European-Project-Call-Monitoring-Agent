#!/usr/bin/env python3
"""
Test with REAL LangGraph routing - shows the Planner loop working!
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

import importlib.util

print("=" * 80)
print("EU CALL FINDER - LANGGRAPH LOOP TEST")
print("With Automatic Routing & Planner Loop")
print("=" * 80)

print("\nLoading modules...")

# Load contracts
spec = importlib.util.spec_from_file_location("contracts", "contracts/schemas.py")
contracts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contracts)

CompanyInput = contracts.CompanyInput
CompanyProfile = contracts.CompanyProfile
Domain = contracts.Domain
DomainLevel = contracts.DomainLevel

# Load state
spec2 = importlib.util.spec_from_file_location("state", "contracts/state.py")
state_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(state_module)

create_initial_state = state_module.create_initial_state

# Load compiled workflow
spec3 = importlib.util.spec_from_file_location(
    "master_agent", "2_orchestration/master_agent.py"
)
master = importlib.util.module_from_spec(spec3)
spec3.loader.exec_module(master)

compile_workflow = master.compile_workflow

print("Modules loaded!")


def test_with_langgraph_routing():
    """Run workflow with LangGraph automatic routing"""

    print("\n" + "=" * 80)
    print("SETUP: Creating Company Profile")
    print("=" * 80)

    company_input = CompanyInput(
        company=CompanyProfile(
            name="AI Solutions Ltd",
            description="Bulgarian AI company developing machine learning solutions for healthcare.",
            type="SME",
            employees=25,
            country="Bulgaria",
            domains=[
                Domain(
                    name="Artificial Intelligence",
                    sub_domains=["Machine Learning"],
                    level=DomainLevel.ADVANCED,
                )
            ],
        )
    )

    print(f"\nCompany: {company_input.company.name}")
    print(f"Country: {company_input.company.country}")

    # Create initial state
    state = create_initial_state(company_input.model_dump())

    print("\n" + "=" * 80)
    print("STARTING LANGGRAPH WORKFLOW")
    print("=" * 80)
    print("\nThis will stream events in real-time...")
    print("Watch for the Planner loop!\n")

    # Compile workflow with automatic routing
    app = compile_workflow()

    # Track iterations
    planner_count = 0
    node_history = []

    # Stream workflow events
    config = {"configurable": {"thread_id": "loop-test-001"}}

    try:
        for event in app.stream(state, config):
            # Get node name from event
            node_name = list(event.keys())[0] if event else "unknown"
            node_history.append(node_name)

            print(f"\n{'=' * 60}")
            print(f"[EVENT] Node completed: {node_name.upper()}")
            print(f"{'=' * 60}")

            # Get current state after this node
            current_state = app.get_state(config)

            if current_state:
                state_values = current_state.values

                if node_name == "safety_check":
                    print(
                        f"  -> Safety passed: {state_values.get('safety_check_passed')}"
                    )

                elif node_name == "planner":
                    planner_count += 1
                    plan = state_values.get("scraper_plan", {})
                    print(f"  -> Planner iteration: {planner_count}")
                    print(f"  -> Search queries: {len(plan.get('search_queries', []))}")
                    print(f"  -> Target: {', '.join(plan.get('target_programs', []))}")

                    # Check if this is a loop iteration
                    if state_values.get("plan_feedback"):
                        print(f"  -> **FEEDBACK FROM ANALYSIS:**")
                        print(f"     {state_values['plan_feedback'][:70]}...")
                        print(f"  -> **LOOPING BACK TO REFINE PLAN**")

                elif node_name == "retrieval":
                    topics = state_values.get("scraped_topics", [])
                    print(f"  -> Topics retrieved: {len(topics)}")
                    if topics:
                        for i, t in enumerate(topics[:3], 1):
                            print(f"     {i}. {t.get('title', 'N/A')[:50]}...")

                elif node_name == "analysis":
                    calls = state_values.get("analyzed_calls", [])
                    summary = state_values.get("analysis_summary", {})
                    approved = state_values.get("plan_approved")

                    print(f"  -> Calls analyzed: {len(calls)}")
                    print(f"  -> Decision: {summary.get('decision', 'N/A').upper()}")
                    print(f"  -> Plan approved: {approved}")

                    if not approved:
                        print(f"  -> **ROUTING DECISION: LOOP BACK TO PLANNER**")
                        print(f"  -> Reason: {summary.get('reasoning', 'N/A')[:60]}...")
                    else:
                        print(f"  -> **ROUTING DECISION: CONTINUE TO REPORTER**")

                elif node_name == "reporter":
                    report = state_values.get("final_report", {})
                    print(
                        f"  -> Report generated: {report.get('total_calls_found', 0)} calls"
                    )
                    print(f"  -> Workflow status: {state_values.get('workflow_status')}")

            # Safety limit
            if planner_count > 5:
                print(f"\n{'=' * 60}")
                print("[SAFETY] Max iterations reached, stopping")
                print(f"{'=' * 60}")
                break

        # Final summary
        print("\n" + "=" * 80)
        print("WORKFLOW EXECUTION COMPLETE")
        print("=" * 80)

        final_state = app.get_state(config)
        if final_state:
            state = final_state.values

            print(f"\n📊 EXECUTION SUMMARY:")
            print(f"   Total nodes executed: {len(node_history)}")
            print(f"   Execution path: {' -> '.join(node_history)}")
            print(f"\n   Planner iterations: {planner_count}")
            print(f"   Topics retrieved: {len(state.get('scraped_topics', []))}")
            print(f"   Calls analyzed: {len(state.get('analyzed_calls', []))}")
            print(f"   Final status: {state.get('workflow_status')}")

            # Show if loop happened
            planner_nodes = [n for n in node_history if n == "planner"]
            if len(planner_nodes) > 1:
                print(f"\n   [OK] PLANNER LOOP DETECTED!")
                print(f"   [OK] Planner ran {len(planner_nodes)} times")
            else:
                print(f"\n   [INFO]  Planner ran once (no loop needed)")

        return True

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + ">" * 40)
    print("LANGGRAPH LOOP TEST")
    print(">" * 40)
    print("\nThis test uses proper LangGraph routing")
    print("You'll see the Planner loop if analysis suggests refinement")

    try:
        success = test_with_langgraph_routing()

        print("\n" + ">" * 40)
        if success:
            print("SUCCESS!")
        else:
            print("TEST FAILED")
        print(">" * 40)

    except KeyboardInterrupt:
        print("\n\nCancelled by user")
    except Exception as e:
        print(f"\n[ERROR] {e}")
