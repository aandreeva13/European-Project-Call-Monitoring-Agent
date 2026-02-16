#!/usr/bin/env python3
"""
CLI Interface for EU Call Finder Workflow WITH FULL STATE DEBUGGING
Shows state at every node during the process
"""

import sys
import os

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv()

import importlib.util
import json
from datetime import datetime
from typing import Dict, Any
import pprint

# Global state tracker
workflow_states = []


def log_state(step_name: str, state: Dict[str, Any], description: str = ""):
    """Log the current state with nice formatting"""
    timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

    print(f"\n{'=' * 80}")
    print(f"[{timestamp}] STATE: {step_name}")
    print(f"{'=' * 80}")

    if description:
        print(f"Description: {description}")
        print("-" * 80)

    # Show key state fields
    key_fields = [
        "company_input",
        "safety_check_passed",
        "scraper_plan",
        "search_terms",
        "scraped_topics",
        "analyzed_calls",
        "plan_approved",
        "plan_feedback",
        "final_report",
        "workflow_status",
    ]

    for field in key_fields:
        if field in state:
            value = state[field]
            if value is None:
                print(f"  {field}: None")
            elif isinstance(value, list):
                print(f"  {field}: [{len(value)} items]")
                if len(value) > 0 and len(str(value[0])) < 100:
                    for i, item in enumerate(value[:3], 1):
                        if isinstance(item, dict) and "title" in item:
                            print(
                                f"    {i}. {item.get('id', 'N/A')}: {item['title'][:60]}..."
                            )
                        elif isinstance(item, dict) and "query" in item:
                            print(f"    {i}. {item['query'][:60]}...")
                        elif isinstance(item, str):
                            print(f"    {i}. {item[:60]}...")
            elif isinstance(value, dict):
                print(f"  {field}: {len(value)} keys")
                for k, v in list(value.items())[:5]:
                    if isinstance(v, str) and len(v) > 60:
                        print(f"    - {k}: {v[:60]}...")
                    else:
                        print(f"    - {k}: {v}")
            elif isinstance(value, bool):
                print(f"  {field}: {'YES' if value else 'NO'}")
            else:
                print(f"  {field}: {value}")

    # Save to global tracker
    workflow_states.append(
        {
            "timestamp": timestamp,
            "step": step_name,
            "state": state,
            "description": description,
        }
    )

    print(f"{'=' * 80}\n")


def main():
    print("=" * 80)
    print("EU CALL FINDER - WORKFLOW WITH FULL STATE DEBUGGING")
    print("=" * 80)
    print("\nThis version shows the complete state at every step.\n")

    # Load modules
    print("Loading modules...")
    spec = importlib.util.spec_from_file_location("contracts", "contracts/schemas.py")
    contracts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contracts)

    spec2 = importlib.util.spec_from_file_location(
        "smart_planner", "3_planning/smart_planner.py"
    )
    planner_module = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(planner_module)

    spec3 = importlib.util.spec_from_file_location(
        "scraper_manager", "4_retrieval/scraper_manager.py"
    )
    scraper_module = importlib.util.module_from_spec(spec3)
    spec3.loader.exec_module(scraper_module)

    spec4 = importlib.util.spec_from_file_location("scorer", "5_analysis/scorer.py")
    scorer_module = importlib.util.module_from_spec(spec4)
    spec4.loader.exec_module(scorer_module)

    spec5 = importlib.util.spec_from_file_location(
        "eligibility", "5_analysis/eligibility.py"
    )
    eligibility_module = importlib.util.module_from_spec(spec5)
    spec5.loader.exec_module(eligibility_module)

    spec6 = importlib.util.spec_from_file_location(
        "llm_critic", "5_analysis/llm_critic.py"
    )
    llm_critic_module = importlib.util.module_from_spec(spec6)
    spec6.loader.exec_module(llm_critic_module)

    spec7 = importlib.util.spec_from_file_location(
        "reflection", "5_analysis/reflection.py"
    )
    reflection_module = importlib.util.module_from_spec(spec7)
    spec7.loader.exec_module(reflection_module)

    print("All modules loaded!\n")

    # STEP 1: Initial State
    print("\n" + "#" * 80)
    print("STEP 1: INITIAL STATE")
    print("#" * 80)

    company_data = {
        "company": {
            "name": "AI Solutions Ltd",
            "description": "Bulgarian AI company developing machine learning solutions for healthcare diagnostics and clinical decision support.",
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

    initial_state = {
        "company_input": company_data,
        "safety_check_passed": None,
        "scraper_plan": None,
        "search_terms": [],
        "scraped_topics": [],
        "analyzed_calls": [],
        "plan_approved": None,
        "plan_feedback": None,
        "final_report": None,
        "workflow_status": "initialized",
        "current_step": "start",
    }

    log_state("INITIAL", initial_state, "Workflow starting with company profile")

    # STEP 2: Safety Check
    print("\n" + "#" * 80)
    print("STEP 2: SAFETY CHECK NODE")
    print("#" * 80)

    company = company_data.get("company", {})
    checks = {
        "name": bool(company.get("name")),
        "description": len(company.get("description", "")) >= 20,
        "domains": len(company.get("domains", [])) > 0,
        "country": bool(company.get("country")),
    }
    safety_passed = all(checks.values())

    state_after_safety = {
        **initial_state,
        "safety_check_passed": safety_passed,
        "workflow_status": "safety_check_complete",
        "current_step": "planner",
    }

    log_state(
        "AFTER SAFETY CHECK",
        state_after_safety,
        f"Safety checks: {checks}, Result: {'PASSED' if safety_passed else 'FAILED'}",
    )

    # STEP 3: Planner Node
    print("\n" + "#" * 80)
    print("STEP 3: PLANNER NODE")
    print("#" * 80)

    plan = planner_module.create_smart_plan(company_data, previous_feedback=None)

    state_after_planner = {
        **state_after_safety,
        "scraper_plan": plan,
        "search_terms": plan["search_queries"],
        "planner_iterations": 1,
        "workflow_status": "planning_complete",
        "current_step": "retrieval",
    }

    log_state(
        "AFTER PLANNER",
        state_after_planner,
        f"Generated {len(plan['search_queries'])} search queries",
    )

    # STEP 4: Retrieval Node (API + Selenium)
    print("\n" + "#" * 80)
    print("STEP 4: RETRIEVAL NODE (API + Selenium)")
    print("#" * 80)
    print("Scraping with API + Selenium... (this may take 1-2 minutes)")

    import requests

    search_url = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"
    headers = {"User-Agent": "Mozilla/5.0"}
    query_data = plan["filter_config"]
    files = {
        "query": ("blob", json.dumps(query_data), "application/json"),
        "displayFields": (
            "blob",
            json.dumps(["identifier", "title"]),
            "application/json",
        ),
    }

    # API Search (fast)
    all_results = []
    unique_topics = {}

    for i, search_term in enumerate(
        plan["search_queries"][:2], 1
    ):  # Use first 2 queries for speed
        params = {
            "apiKey": "SEDIA",
            "text": search_term,
            "pageSize": "5",
            "pageNumber": "1",
        }
        try:
            response = requests.post(
                search_url, params=params, files=files, headers=headers, timeout=30
            )
            data = response.json()
            results = data.get("results", [])

            for item in results:
                meta = item.get("metadata", {})
                topic_id = meta.get("identifier", [""])[0]
                title = meta.get("title", [""])[0] if meta.get("title") else "N/A"
                if topic_id and topic_id not in unique_topics:
                    unique_topics[topic_id] = {
                        "id": topic_id,
                        "title": title,
                        "programme": "Unknown",
                    }

            all_results.extend(results)
        except Exception as e:
            print(f"  Query {i} error: {e}")

    scraped_topics = list(unique_topics.values())

    state_after_retrieval = {
        **state_after_planner,
        "scraped_topics": scraped_topics,
        "workflow_status": "retrieval_complete",
        "current_step": "analysis",
    }

    log_state(
        "AFTER RETRIEVAL",
        state_after_retrieval,
        f"Retrieved {len(scraped_topics)} unique topics via API",
    )

    # STEP 5: Analysis Node
    print("\n" + "#" * 80)
    print("STEP 5: ANALYSIS NODE")
    print("#" * 80)

    if not scraped_topics:
        print("No topics to analyze!")
        analyzed_calls = []
        reflection_decision = "finalize"
    else:
        analyzed_calls = []
        company_profile = company_data.get("company", {})

        print(f"\nAnalyzing {len(scraped_topics)} calls...")
        for i, topic in enumerate(scraped_topics, 1):
            print(f"\n  [{i}/{len(scraped_topics)}] {topic['title'][:50]}...")

            # Eligibility
            eligibility = eligibility_module.apply_eligibility_filters(
                topic, company_profile
            )

            # Scoring
            scoring = scorer_module.score_call(topic, company_profile, {})

            # LLM Critic
            qualitative = llm_critic_module.perform_qualitative_analysis(
                topic, company_profile
            )

            analyzed_calls.append(
                {
                    "id": topic["id"],
                    "title": topic["title"],
                    "score": scoring["total"],
                    "eligible": eligibility["all_passed"],
                    "match_summary": qualitative.get("match_summary", "N/A")[:80],
                    "keyword_hits": qualitative.get("keyword_hits", []),
                    "analysis_method": qualitative.get("analysis_method", "rule_based"),
                }
            )

            print(f"    Score: {scoring['total']}/10")
            print(f"    Eligible: {'Yes' if eligibility['all_passed'] else 'No'}")
            print(f"    Match: {qualitative.get('match_summary', 'N/A')[:50]}...")

        # Reflection
        print("\n" + "-" * 80)
        print("REFLECTION MODULE OUTPUT:")
        print("-" * 80)

        search_params = {"max_results": 10, "portals": ["ftop", "eufunds_bg"]}
        reflection = reflection_module.reflect_on_results(
            analyzed_calls, search_params, iteration=1
        )

        print(f"DECISION: {reflection['decision'].upper()}")
        print(f"REASONING: {reflection['reasoning']}")
        print(f"STATS:")
        print(f"  - Total results: {reflection['stats']['total_results']}")
        print(f"  - High scores (8+): {reflection['stats']['high_scores']}")
        print(f"  - Medium scores (6-8): {reflection['stats']['medium_scores']}")
        print(f"  - Low scores (<6): {reflection['stats']['low_scores']}")
        print(f"  - Average score: {reflection['stats']['average_score']:.1f}/10")

        if reflection.get("recommendations"):
            print(f"RECOMMENDATIONS:")
            for rec in reflection["recommendations"]:
                print(f"  - {rec}")

        reflection_decision = reflection["decision"]
        feedback = (
            "; ".join(reflection.get("recommendations", []))
            if reflection.get("recommendations")
            else None
        )

    state_after_analysis = {
        **state_after_retrieval,
        "analyzed_calls": analyzed_calls,
        "plan_approved": reflection_decision != "refine",
        "plan_feedback": feedback if reflection_decision == "refine" else None,
        "workflow_status": "analysis_complete",
        "current_step": "reporter" if reflection_decision != "refine" else "planner",
    }

    log_state(
        "AFTER ANALYSIS",
        state_after_analysis,
        f"Analyzed {len(analyzed_calls)} calls, Decision: {reflection_decision.upper()}",
    )

    # STEP 6: Reporter Node
    print("\n" + "#" * 80)
    print("STEP 6: REPORTER NODE")
    print("#" * 80)

    report = {
        "company_name": company_data["company"]["name"],
        "total_calls": len(analyzed_calls),
        "timestamp": datetime.now().isoformat(),
        "calls": analyzed_calls,
    }

    state_final = {
        **state_after_analysis,
        "final_report": report,
        "workflow_status": "completed",
        "current_step": "end",
    }

    log_state("FINAL STATE", state_final, "Workflow completed successfully")

    # Print summary
    print("\n" + "=" * 80)
    print("WORKFLOW COMPLETE - SUMMARY")
    print("=" * 80)
    print(f"Total state transitions: {len(workflow_states)}")
    print(f"Steps executed:")
    for i, state_info in enumerate(workflow_states, 1):
        print(f"  {i}. {state_info['step']}")

    print(f"\nFinal Results:")
    print(f"  - Calls analyzed: {len(analyzed_calls)}")
    print(f"  - Workflow status: {state_final['workflow_status']}")

    if analyzed_calls:
        print(f"\nTop Call:")
        best = max(analyzed_calls, key=lambda x: x["score"])
        print(f"  {best['title'][:60]}...")
        print(f"  Score: {best['score']}/10")

    # Save state history
    state_file = f"workflow_states_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(state_file, "w", encoding="utf-8") as f:
        # Convert to serializable format
        serializable_states = []
        for s in workflow_states:
            serializable_states.append(
                {
                    "timestamp": s["timestamp"],
                    "step": s["step"],
                    "description": s["description"],
                    "state_keys": list(s["state"].keys()),
                }
            )
        json.dump(serializable_states, f, indent=2)

    print(f"\nState history saved to: {state_file}")


if __name__ == "__main__":
    main()
