#!/usr/bin/env python3
"""
Test script for the LangGraph workflow.
"""

import sys
import os

# Setup path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv()

from contracts.schemas import CompanyInput, CompanyProfile, Domain, DomainLevel
from contracts.state import create_initial_state, get_state_summary

# Import workflow
from orchestration.master_agent import (
    create_workflow,
    compile_workflow,
    run_workflow,
    safety_check_node,
    planner_node,
    analysis_node,
)


def test_workflow_structure():
    """Test that the workflow graph is correctly structured."""
    print("=" * 70)
    print("TEST 1: Workflow Structure")
    print("=" * 70)

    workflow = create_workflow()
    print("\n✅ Workflow created successfully")

    # Compile it
    app = compile_workflow()
    print("✅ Workflow compiled successfully")

    # Try to get graph visualization
    try:
        # This will show the graph structure
        print("\n📊 Workflow Graph Structure:")
        print("   Entry: safety_check")
        print("   Flow: safety_check → planner → retrieval → analysis")
        print("   Loop: analysis → planner (if results poor)")
        print("   Exit: analysis → reporter → END")
        print("   Fail: safety_check → END (if validation fails)")
    except Exception as e:
        print(f"   Graph info: {e}")

    return True


def test_safety_node():
    """Test safety check node with valid input."""
    print("\n" + "=" * 70)
    print("TEST 2: Safety Check Node")
    print("=" * 70)

    company_input = CompanyInput(
        company=CompanyProfile(
            name="AI Startup",
            description="We develop artificial intelligence solutions for healthcare.",
            type="SME",
            employees=25,
            country="Bulgaria",
            domains=[Domain(name="AI", sub_domains=["ML"], level=DomainLevel.ADVANCED)],
        )
    )

    initial_state = create_initial_state(company_input.model_dump())
    result = safety_check_node(initial_state)

    print(f"\nSafety check passed: {result['safety_check_passed']}")
    print(f"Current step: {result['current_step']}")

    if result["validation_result"]:
        print(f"Validation score: {result['validation_result'].get('score', 'N/A')}")

    return result["safety_check_passed"]


def test_planner_node():
    """Test planner node."""
    print("\n" + "=" * 70)
    print("TEST 3: Planner Node")
    print("=" * 70)

    company_input = CompanyInput(
        company=CompanyProfile(
            name="GreenTech Germany",
            description="German company specializing in renewable energy solutions and smart grid technology.",
            type="SME",
            employees=40,
            country="Germany",
            domains=[
                Domain(
                    name="Renewable Energy",
                    sub_domains=["Solar", "Wind", "Smart Grid"],
                    level=DomainLevel.EXPERT,
                )
            ],
        )
    )

    initial_state = create_initial_state(company_input.model_dump())
    initial_state["safety_check_passed"] = True

    result = planner_node(initial_state)

    print(f"\nPlan created: {result['scraper_plan'] is not None}")
    if result["scraper_plan"]:
        plan = result["scraper_plan"]
        print(f"Search queries: {len(plan.get('search_queries', []))}")
        print(f"Target programs: {plan.get('target_programs', [])}")
        print(f"Estimated calls: {plan.get('estimated_calls', 0)}")

    return result["scraper_plan"] is not None


def test_analysis_decision():
    """Test analysis node decision logic."""
    print("\n" + "=" * 70)
    print("TEST 4: Analysis Decision Logic")
    print("=" * 70)

    # Test 1: No results - should loop back to planner
    print("\nTest 4a: No scraped topics (should loop to planner)")
    state_no_results = create_initial_state({})
    state_no_results["scraped_topics"] = []
    state_no_results["planner_iterations"] = 1
    state_no_results["max_planner_iterations"] = 3

    result = analysis_node(state_no_results)
    print(f"   Plan approved: {result['plan_approved']}")
    print(f"   Next step: {result['current_step']}")
    print(f"   Feedback: {result.get('plan_feedback', 'N/A')[:50]}...")

    should_loop = not result["plan_approved"] and result["current_step"] == "planning"

    # Test 2: Has results - should continue to reporter
    print("\nTest 4b: Has scraped topics (should go to reporter)")
    state_with_results = create_initial_state({})
    state_with_results["scraped_topics"] = [
        {"id": "TEST-001", "title": "Test Call 1"},
        {"id": "TEST-002", "title": "Test Call 2"},
    ]

    result2 = analysis_node(state_with_results)
    print(f"   Plan approved: {result2['plan_approved']}")
    print(f"   Next step: {result2['current_step']}")
    print(f"   Analyzed calls: {len(result2.get('analyzed_calls', []))}")

    should_continue = (
        result2["plan_approved"] and result2["current_step"] == "reporting"
    )

    return should_loop and should_continue


def test_full_workflow():
    """Test complete workflow execution."""
    print("\n" + "=" * 70)
    print("TEST 5: Full Workflow Execution")
    print("=" * 70)

    company_input = CompanyInput(
        company=CompanyProfile(
            name="Test Company",
            description="Bulgarian AI company developing machine learning solutions.",
            type="SME",
            employees=30,
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

    print("\n🚀 Running full workflow...")
    print("   (This will use fallback mode for scraping)")

    try:
        result = run_workflow(company_input.model_dump(), thread_id="test-run-001")

        print("\n" + "=" * 70)
        print("WORKFLOW RESULTS")
        print("=" * 70)

        summary = get_state_summary(result)
        print(f"\nStatus: {summary['status']}")
        print(f"Final step: {summary['current_step']}")
        print(f"Planner iterations: {summary['planner_iterations']}")
        print(f"Topics found: {summary['topics_found']}")
        print(f"Calls analyzed: {summary['calls_analyzed']}")
        print(f"Errors: {summary['errors']}")

        if result.get("final_report"):
            print("\n📊 Final Report Summary:")
            report = result["final_report"]
            print(f"   Company: {report.get('company_name')}")
            print(f"   Total calls: {report.get('total_calls_found')}")
            print(f"   Summary: {report.get('summary')}")

        return result.get("workflow_status") == "completed"

    except Exception as e:
        print(f"\n❌ Workflow failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


def print_workflow_diagram():
    """Print ASCII workflow diagram."""
    print("\n" + "=" * 70)
    print("WORKFLOW DIAGRAM")
    print("=" * 70)
    print("""
    ┌─────────────────────────────────────────────────────────────┐
    │                      EU CALL FINDER                          │
    │                     LangGraph Workflow                       │
    └─────────────────────────────────────────────────────────────┘
    
    ┌──────────────┐
    │   START      │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐     Fail      ┌──────────┐
    │ SAFETY CHECK │ ─────────────▶ │   END    │
    │  + Validate  │                │ (Failed) │
    └──────┬───────┘                └──────────┘
           │ Pass
           ▼
    ┌──────────────┐
    │   PLANNER    │◄────────────────────┐
    │ Create Plan  │                     │
    └──────┬───────┘                     │
           │                             │
           ▼                             │ Loop
    ┌──────────────┐                     │ if poor
    │  RETRIEVAL   │                     │ results
    │ Scrape Data  │                     │
    └──────┬───────┘                     │
           │                             │
           ▼                             │
    ┌──────────────┐     Poor     ┌──────┴───────┐
    │   ANALYSIS   │ ────────────▶│ Plan Refine  │
    │Evaluate Data │               │  Feedback    │
    └──────┬───────┘               └──────────────┘
           │ Good
           ▼
    ┌──────────────┐
    │   REPORTER   │
    │Build Report  │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │    END       │
    │ (Completed)  │
    └──────────────┘
    """)


if __name__ == "__main__":
    print("\n" + "🚀" * 35)
    print("EU CALL FINDER - WORKFLOW TEST SUITE")
    print("🚀" * 35)

    results = []

    # Run tests
    try:
        results.append(("Workflow Structure", test_workflow_structure()))
    except Exception as e:
        print(f"\n❌ Workflow structure test failed: {e}")
        results.append(("Workflow Structure", False))

    try:
        results.append(("Safety Node", test_safety_node()))
    except Exception as e:
        print(f"\n❌ Safety node test failed: {e}")
        results.append(("Safety Node", False))

    try:
        results.append(("Planner Node", test_planner_node()))
    except Exception as e:
        print(f"\n❌ Planner node test failed: {e}")
        results.append(("Planner Node", False))

    try:
        results.append(("Analysis Decision", test_analysis_decision()))
    except Exception as e:
        print(f"\n❌ Analysis decision test failed: {e}")
        results.append(("Analysis Decision", False))

    # Full workflow test (optional - takes longer)
    print("\n" + "=" * 70)
    print("OPTIONAL: Full Workflow Test")
    print("=" * 70)
    print("Skip full workflow test? (y/n): ", end="")
    try:
        response = input().strip().lower()
        if response != "y":
            try:
                results.append(("Full Workflow", test_full_workflow()))
            except Exception as e:
                print(f"\n❌ Full workflow test failed: {e}")
                results.append(("Full Workflow", False))
        else:
            print("   Skipped.")
    except EOFError:
        print("y")
        print("   Skipped (non-interactive mode).")

    # Print diagram
    print_workflow_diagram()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
