#!/usr/bin/env python3
"""
Simple test for the LangGraph workflow using direct imports.
"""

import sys
import os
import importlib.util

# Setup path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv()

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

# Load master agent
spec3 = importlib.util.spec_from_file_location(
    "master_agent", "2_orchestration/master_agent.py"
)
master = importlib.util.module_from_spec(spec3)
spec3.loader.exec_module(master)

safety_check_node = master.safety_check_node
planner_node = master.planner_node
analysis_node = master.analysis_node


def test_safety_node():
    print("=" * 70)
    print("TEST: Safety Check Node")
    print("=" * 70)

    company = CompanyInput(
        company=CompanyProfile(
            name="AI Startup",
            description="We develop AI solutions for healthcare.",
            type="SME",
            employees=25,
            country="Bulgaria",
            domains=[Domain(name="AI", sub_domains=["ML"], level=DomainLevel.ADVANCED)],
        )
    )

    state = create_initial_state(company.model_dump())
    result = safety_check_node(state)

    print(f"\n✅ Safety check passed: {result['safety_check_passed']}")
    print(f"   Current step: {result['current_step']}")

    return result["safety_check_passed"]


def test_planner_node():
    print("\n" + "=" * 70)
    print("TEST: Planner Node")
    print("=" * 70)

    company = CompanyInput(
        company=CompanyProfile(
            name="GreenTech",
            description="Renewable energy company.",
            type="SME",
            employees=40,
            country="Germany",
            domains=[
                Domain(name="Energy", sub_domains=["Solar"], level=DomainLevel.EXPERT)
            ],
        )
    )

    state = create_initial_state(company.model_dump())
    state["safety_check_passed"] = True

    result = planner_node(state)

    if result.get("scraper_plan"):
        plan = result["scraper_plan"]
        print(f"\n✅ Plan created!")
        print(f"   Queries: {len(plan.get('search_queries', []))}")
        print(f"   Programs: {plan.get('target_programs', [])}")
        print(f"   Estimated: {plan.get('estimated_calls', 0)} calls")
        return True

    return False


def test_analysis_loop():
    print("\n" + "=" * 70)
    print("TEST: Analysis Loop (Planner ↔ Analysis)")
    print("=" * 70)

    # Test 1: No results → loop back
    print("\nScenario 1: No results → should loop to planner")
    state = create_initial_state({})
    state["scraped_topics"] = []
    state["planner_iterations"] = 1
    state["max_planner_iterations"] = 3

    result = analysis_node(state)

    print(f"   Plan approved: {result['plan_approved']}")
    print(f"   Next step: {result['current_step']}")

    loops_correctly = (
        not result["plan_approved"] and result["current_step"] == "planning"
    )

    # Test 2: Has results → continue
    print("\nScenario 2: Has results → should continue")
    state2 = create_initial_state({})
    state2["scraped_topics"] = [
        {"id": "HORIZON-001", "title": "AI Research Grant"},
        {"id": "DIGITAL-002", "title": "Digital Innovation"},
    ]

    result2 = analysis_node(state2)

    print(f"   Plan approved: {result2['plan_approved']}")
    print(f"   Next step: {result2['current_step']}")
    print(f"   Analyzed: {len(result2.get('analyzed_calls', []))} calls")

    continues_correctly = (
        result2["plan_approved"] and result2["current_step"] == "reporting"
    )

    return loops_correctly and continues_correctly


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("LANGGRAPH WORKFLOW TESTS")
    print("=" * 70)

    results = []

    try:
        results.append(("Safety Node", test_safety_node()))
    except Exception as e:
        print(f"\n❌ Error: {e}")
        results.append(("Safety Node", False))

    try:
        results.append(("Planner Node", test_planner_node()))
    except Exception as e:
        print(f"\n❌ Error: {e}")
        results.append(("Planner Node", False))

    try:
        results.append(("Analysis Loop", test_analysis_loop()))
    except Exception as e:
        print(f"\n❌ Error: {e}")
        results.append(("Analysis Loop", False))

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"{status} {name}")

    passed_count = sum(1 for _, p in results if p)
    print(f"\n{passed_count}/{len(results)} tests passed")

    if passed_count == len(results):
        print("\n🎉 All workflow components working!")
