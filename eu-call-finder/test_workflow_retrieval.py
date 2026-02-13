#!/usr/bin/env python3
"""
Test workflow up to and including retrieval.
Shows actual results from web scraping.
"""

import sys
import os
import json

# Setup path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv()

print("Loading modules...")

# Load contracts
import importlib.util

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
get_state_summary = state_module.get_state_summary

# Load master agent nodes
spec3 = importlib.util.spec_from_file_location(
    "master_agent", "2_orchestration/master_agent.py"
)
master = importlib.util.module_from_spec(spec3)
spec3.loader.exec_module(master)

safety_check_node = master.safety_check_node
planner_node = master.planner_node
retrieval_node = master.retrieval_node


def test_workflow_until_retrieval():
    """Run workflow: Safety → Planner → Retrieval"""
    print("\n" + "=" * 70)
    print("EU CALL FINDER - WORKFLOW TEST (Safety → Planner → Retrieval)")
    print("=" * 70)

    # Step 0: Create company input
    print("\n📋 STEP 0: Creating Company Input")
    print("-" * 70)

    company_input = CompanyInput(
        company=CompanyProfile(
            name="NexGen AI Solutions",
            description="Bulgarian AI company developing intelligent automation solutions for enterprise clients. Specialized in LLM applications, agentic AI and NLP. We build custom AI agents for business process automation.",
            type="SME",
            employees=45,
            country="Bulgaria",
            city="Sofia",
            domains=[
                Domain(
                    name="Artificial Intelligence",
                    sub_domains=["Machine Learning", "NLP", "Agentic AI"],
                    level=DomainLevel.ADVANCED,
                ),
                Domain(
                    name="Process Automation",
                    sub_domains=["Business Automation"],
                    level=DomainLevel.ADVANCED,
                ),
            ],
        )
    )

    print(f"Company: {company_input.company.name}")
    print(f"Type: {company_input.company.type}")
    print(f"Country: {company_input.company.country}")
    print(f"Domains: {len(company_input.company.domains)}")
    for d in company_input.company.domains:
        print(f"  - {d.name}: {', '.join(d.sub_domains)}")

    # Create initial state
    state = create_initial_state(company_input.model_dump())

    # Step 1: Safety Check
    print("\n" + "=" * 70)
    print("STEP 1: SAFETY CHECK & VALIDATION")
    print("=" * 70)

    state = safety_check_node(state)

    if not state["safety_check_passed"]:
        print(f"\n❌ FAILED: {state.get('error_message', 'Safety check failed')}")
        return False

    print(f"\n✅ Safety check passed")
    print(f"   Validation score: {state['validation_result'].get('score', 'N/A')}/10")
    print(f"   Next step: {state['current_step']}")

    # Step 2: Planning
    print("\n" + "=" * 70)
    print("STEP 2: PLANNING")
    print("=" * 70)

    state = planner_node(state)

    if not state.get("scraper_plan"):
        print(f"\n❌ Planning failed")
        return False

    plan = state["scraper_plan"]
    print(f"\n✅ Plan created!")
    print(f"\n📊 Plan Details:")
    print(f"   Company: {plan['company_name']}")
    print(f"   Type: {plan['company_type']}")
    print(f"   Target Programs: {', '.join(plan['target_programs'])}")
    print(f"   Estimated Calls: {plan['estimated_calls']}")
    print(f"\n🔍 Search Queries ({len(plan['search_queries'])}):")
    for i, query in enumerate(plan["search_queries"], 1):
        print(f"   {i}. {query}")

    print(f"\n📋 Static Filter Config (for EU Portal):")
    print(json.dumps(plan["filter_config"], indent=4))

    print(f"\n💡 Reasoning:")
    print(f"   {plan['reasoning']}")

    print(f"\n   Next step: {state['current_step']}")

    # Step 3: Retrieval
    print("\n" + "=" * 70)
    print("STEP 3: RETRIEVAL / WEB SCRAPING")
    print("=" * 70)
    print("\n⚠️  This will scrape the EU Funding Portal...")
    print("   Search terms:", state["search_terms"])
    print("\n   Starting retrieval (this may take 1-3 minutes)...")
    print("   (Press Ctrl+C to cancel)")

    try:
        state = retrieval_node(state)

        print(f"\n✅ Retrieval completed!")
        print(f"\n📈 Results:")
        print(f"   Topics found: {len(state['scraped_topics'])}")

        if state["scraped_topics"]:
            print(f"\n   First 3 topics:")
            for i, topic in enumerate(state["scraped_topics"][:3], 1):
                print(f"\n   [{i}] {topic.get('id', 'N/A')}")
                print(f"       Title: {topic.get('title', 'N/A')[:80]}...")
                print(f"       Status: {topic.get('status', 'N/A')}")
                print(
                    f"       Programme: {topic.get('general_info', {}).get('programme', 'N/A')}"
                )
                deadline = (
                    topic.get("general_info", {})
                    .get("dates", {})
                    .get("deadline", "N/A")
                )
                print(f"       Deadline: {deadline}")

                # Show description preview
                desc = topic.get("content", {}).get("description", "")
                if desc and desc != "N/A":
                    print(f"       Description: {desc[:100]}...")
        else:
            print("\n   No topics found. This could mean:")
            print("   - No matching calls currently open")
            print("   - Search terms too specific")
            print("   - EU portal temporarily unavailable")

        if state.get("retrieval_errors"):
            print(f"\n⚠️  Retrieval errors: {state['retrieval_errors']}")

        # Summary
        print("\n" + "=" * 70)
        print("WORKFLOW SUMMARY (Up to Retrieval)")
        print("=" * 70)

        summary = get_state_summary(state)
        print(f"\nStatus: {summary['status']}")
        print(f"Current step: {summary['current_step']}")
        print(f"Planner iterations: {summary['planner_iterations']}")
        print(f"Topics found: {summary['topics_found']}")
        print(f"Errors: {summary['errors']}")

        print("\n" + "=" * 70)
        print("✅ WORKFLOW TEST COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(f"\nNext would be: Analysis → [Planner loop if needed] → Reporter")

        return True

    except KeyboardInterrupt:
        print("\n\n⚠️  Retrieval cancelled by user")
        return False
    except Exception as e:
        print(f"\n❌ Retrieval failed: {str(e)}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "🚀" * 35)
    print("EU CALL FINDER - RETRIEVAL TEST")
    print("🚀" * 35)

    print("\nThis test will:")
    print("  1. Validate a company profile")
    print("  2. Create a search plan using LLM")
    print("  3. Scrape the EU Funding Portal (real data)")
    print("\nNote: Step 3 may take 1-3 minutes depending on results")

    try:
        success = test_workflow_until_retrieval()

        if success:
            print("\n🎉 All steps completed successfully!")
        else:
            print("\n❌ Test failed or was cancelled")

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback

        traceback.print_exc()
