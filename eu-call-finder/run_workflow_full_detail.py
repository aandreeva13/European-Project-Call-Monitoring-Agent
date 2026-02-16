#!/usr/bin/env python3
"""
CLI Interface with FULL DETAILED OUTPUT
Shows complete information from retrieval like robotics_final_detailed.json
"""

import sys
import os

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv()

import importlib.util
import json
from datetime import datetime


def print_section(title, char="="):
    """Print a section header"""
    print(f"\n{char * 80}")
    print(f"{title}")
    print(f"{char * 80}\n")


def print_call_detail(call, index):
    """Print full call details in JSON-like format"""
    print(f"Call {index}:")
    print(f"  ID: {call.get('id', 'N/A')}")
    print(f"  Title: {call.get('title', 'N/A')}")
    print(f"  URL: {call.get('url', 'N/A')}")
    print(f"  Status: {call.get('status', 'N/A')}")

    # General Info
    general = call.get("general_info", {})
    print(f"\n  General Info:")
    print(f"    Programme: {general.get('programme', 'N/A')}")
    print(f"    Call: {general.get('call', 'N/A')}")
    print(f"    Action Type: {general.get('action_type', 'N/A')}")
    print(f"    Deadline Model: {general.get('deadline_model', 'N/A')}")
    dates = general.get("dates", {})
    print(f"    Opening: {dates.get('opening', 'N/A')}")
    print(f"    Deadline: {dates.get('deadline', 'N/A')}")

    # Content
    content = call.get("content", {})
    print(f"\n  Content:")
    desc = content.get("description", "N/A")
    print(
        f"    Description: {desc[:200]}..."
        if len(str(desc)) > 200
        else f"    Description: {desc}"
    )

    dest = content.get("destination", "N/A")
    print(
        f"    Destination: {dest[:150]}..."
        if len(str(dest)) > 150
        else f"    Destination: {dest}"
    )

    cond = content.get("conditions", "N/A")
    print(
        f"    Conditions: {cond[:150]}..."
        if len(str(cond)) > 150
        else f"    Conditions: {cond}"
    )

    budget = content.get("budget_overview", "N/A")
    print(
        f"    Budget Overview: {budget[:150]}..."
        if len(str(budget)) > 150
        else f"    Budget Overview: {budget}"
    )

    # Partners
    partners = call.get("partners", [])
    print(f"\n  Partners: {len(partners)} announcements")
    if partners:
        for i, partner in enumerate(partners[:3], 1):
            print(
                f"    {i}. {partner.get('organization', 'N/A')} ({partner.get('country', 'N/A')})"
            )

    print("\n" + "-" * 80 + "\n")


def main():
    print_section("EU CALL FINDER - FULL DETAILED OUTPUT", "=")

    # Load modules
    print("Loading modules...")
    spec = importlib.util.spec_from_file_location(
        "smart_planner", "3_planning/smart_planner.py"
    )
    planner_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(planner_module)

    spec2 = importlib.util.spec_from_file_location(
        "scraper_manager", "4_retrieval/scraper_manager.py"
    )
    scraper_module = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(scraper_module)

    spec3 = importlib.util.spec_from_file_location("scorer", "5_analysis/scorer.py")
    scorer_module = importlib.util.module_from_spec(spec3)
    spec3.loader.exec_module(scorer_module)

    spec4 = importlib.util.spec_from_file_location(
        "eligibility", "5_analysis/eligibility.py"
    )
    eligibility_module = importlib.util.module_from_spec(spec4)
    spec4.loader.exec_module(eligibility_module)

    spec5 = importlib.util.spec_from_file_location(
        "llm_critic", "5_analysis/llm_critic.py"
    )
    llm_critic_module = importlib.util.module_from_spec(spec5)
    spec5.loader.exec_module(llm_critic_module)

    spec6 = importlib.util.spec_from_file_location(
        "reflection", "5_analysis/reflection.py"
    )
    reflection_module = importlib.util.module_from_spec(spec6)
    spec6.loader.exec_module(reflection_module)
    print("All modules loaded!\n")

    # Get input
    print_section("STEP 1: COMPANY INPUT", "#")

    company_data = {
        "company": {
            "name": "AI Solutions Ltd",
            "description": "Bulgarian AI company developing machine learning solutions for healthcare diagnostics and clinical decision support systems.",
            "type": "SME",
            "employees": 25,
            "country": "Bulgaria",
            "domains": [
                {
                    "name": "Artificial Intelligence",
                    "sub_domains": ["Machine Learning"],
                    "level": "advanced",
                }
            ],
        }
    }

    print(f"Company: {company_data['company']['name']}")
    print(f"Type: {company_data['company']['type']}")
    print(f"Country: {company_data['company']['country']}")
    print(f"Description: {company_data['company']['description'][:80]}...")

    # Planning
    print_section("STEP 2: SMART PLANNER", "#")
    plan = planner_module.create_smart_plan(company_data)

    print(f"Generated {len(plan['search_queries'])} queries:")
    for i, q in enumerate(plan["search_queries"], 1):
        print(f"  {i}. {q}")
    print(f"\nTarget Programs: {plan['target_programs']}")

    # Retrieval with FULL details
    print_section("STEP 3: RETRIEVAL - FULL CALL DETAILS", "#")
    print("Scraping with API + Selenium...\n")

    topics = scraper_module.scrape_topics_to_json(
        search_terms=plan["search_queries"][:2],  # First 2 queries for speed
        search_query=plan["filter_config"],
        headless=True,
        max_topics=3,
    )

    print(f"RETRIEVED {len(topics)} CALLS WITH COMPLETE DETAILS:\n")
    print(f"State: scraped_topics = {len(topics)} items\n")

    for i, topic in enumerate(topics, 1):
        print_call_detail(topic, i)

    # Save to file
    output_file = f"retrieved_calls_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(topics, f, indent=2, ensure_ascii=False)
    print(f"\nFull calls saved to: {output_file}")

    # Analysis
    print_section("STEP 4: ANALYSIS", "#")

    if topics:
        company_profile = company_data.get("company", {})
        analyzed = []

        for i, topic in enumerate(topics, 1):
            print(f"\nAnalyzing Call {i}: {topic['id']}")
            print("-" * 80)

            eligibility = eligibility_module.apply_eligibility_filters(
                topic, company_profile
            )
            scoring = scorer_module.score_call(topic, company_profile, {})
            qualitative = llm_critic_module.perform_qualitative_analysis(
                topic, company_profile
            )

            print(f"  Eligibility: {'PASS' if eligibility['all_passed'] else 'FAIL'}")
            print(f"  Score: {scoring['total']}/10")
            print(
                f"  Match Summary: {qualitative.get('match_summary', 'N/A')[:100]}..."
            )
            print(f"  Keywords: {', '.join(qualitative.get('keyword_hits', [])[:5])}")

            analyzed.append(
                {
                    "call": topic,
                    "score": scoring["total"],
                    "eligible": eligibility["all_passed"],
                    "analysis": qualitative,
                }
            )

        # Reflection
        print("\n" + "=" * 80)
        print("REFLECTION MODULE:")
        print("=" * 80)

        search_params = {"max_results": 10, "portals": ["ftop", "eufunds_bg"]}
        reflection = reflection_module.reflect_on_results(analyzed, search_params, 1)

        print(f"\nDecision: {reflection['decision'].upper()}")
        print(f"Reasoning: {reflection['reasoning']}")
        print(f"\nStats:")
        print(f"  Total: {reflection['stats']['total_results']}")
        print(f"  High (8+): {reflection['stats']['high_scores']}")
        print(f"  Medium (6-8): {reflection['stats']['medium_scores']}")
        print(f"  Low (<6): {reflection['stats']['low_scores']}")
        print(f"  Average: {reflection['stats']['average_score']:.1f}/10")

        if reflection.get("recommendations"):
            print(f"\nRecommendations:")
            for rec in reflection["recommendations"]:
                print(f"  - {rec}")

    print_section("WORKFLOW COMPLETE", "=")
    print(f"Retrieved {len(topics)} calls with full details")
    print(f"Files saved: {output_file}")


if __name__ == "__main__":
    main()
