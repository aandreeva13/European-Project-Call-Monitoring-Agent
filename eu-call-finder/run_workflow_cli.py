#!/usr/bin/env python3
"""
CLI Interface for EU Call Finder Workflow
Run complete workflow from terminal with user input
"""

import sys
import os

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv()

import importlib.util
import json
from datetime import datetime
from typing import List, Dict, Any


def load_modules():
    """Load all required modules"""
    print("Loading modules...")

    # Contracts
    spec = importlib.util.spec_from_file_location("contracts", "contracts/schemas.py")
    contracts = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(contracts)

    # State
    spec2 = importlib.util.spec_from_file_location("state", "contracts/state.py")
    state_module = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(state_module)

    # SmartPlanner
    spec3 = importlib.util.spec_from_file_location(
        "smart_planner", "3_planning/smart_planner.py"
    )
    planner_module = importlib.util.module_from_spec(spec3)
    spec3.loader.exec_module(planner_module)

    # Scraper
    spec4 = importlib.util.spec_from_file_location(
        "scraper_manager", "4_retrieval/scraper_manager.py"
    )
    scraper_module = importlib.util.module_from_spec(spec4)
    spec4.loader.exec_module(scraper_module)

    # Analysis modules
    spec5 = importlib.util.spec_from_file_location("scorer", "5_analysis/scorer.py")
    scorer_module = importlib.util.module_from_spec(spec5)
    spec5.loader.exec_module(scorer_module)

    spec6 = importlib.util.spec_from_file_location(
        "eligibility", "5_analysis/eligibility.py"
    )
    eligibility_module = importlib.util.module_from_spec(spec6)
    spec6.loader.exec_module(eligibility_module)

    return (
        contracts,
        state_module,
        planner_module,
        scraper_module,
        scorer_module,
        eligibility_module,
    )


def get_company_input_interactive():
    """Get company details interactively from user"""
    print("\n" + "=" * 80)
    print("EU CALL FINDER - COMPANY PROFILE INPUT")
    print("=" * 80)
    print("\nPlease enter your company details:\n")

    # Required fields
    name = input("Company Name: ").strip()
    while not name:
        print("Company name is required!")
        name = input("Company Name: ").strip()

    print("\nCompany Description (what does your company do?):")
    print("(Press Enter twice when done)")
    description_lines = []
    while True:
        line = input()
        if line == "" and description_lines and description_lines[-1] == "":
            break
        description_lines.append(line)
    description = "\n".join(description_lines).strip()
    while len(description) < 20:
        print("Description must be at least 20 characters!")
        description = input("Company Description: ").strip()

    company_type = (
        input("\nCompany Type (SME/Corporation/Startup/Research): ").strip() or "SME"
    )
    country = input("Country: ").strip() or "Bulgaria"

    try:
        employees = int(input("Number of Employees: ").strip() or "25")
    except:
        employees = 25

    # Domains
    print("\nTechnology Domains (comma-separated):")
    print("Examples: Artificial Intelligence, Healthcare, Blockchain, Clean Energy")
    domains_input = input("Domains: ").strip()
    domains = []
    if domains_input:
        for domain_name in domains_input.split(","):
            domain_name = domain_name.strip()
            if domain_name:
                subdomains = input(
                    f"  Sub-domains for {domain_name} (comma-separated, or press Enter): "
                ).strip()
                subdomains_list = (
                    [s.strip() for s in subdomains.split(",")] if subdomains else []
                )
                domains.append(
                    {
                        "name": domain_name,
                        "sub_domains": subdomains_list,
                        "level": "advanced",
                    }
                )

    # Optional fields
    print("\nOptional Fields (press Enter to skip):")
    website = input("Website: ").strip()
    founded = input("Founded Year: ").strip()

    company_data = {
        "company": {
            "name": name,
            "description": description,
            "type": company_type,
            "country": country,
            "employees": employees,
            "domains": domains
            if domains
            else [{"name": "Technology", "sub_domains": [], "level": "intermediate"}],
        }
    }

    if website:
        company_data["company"]["website"] = website
    if founded:
        try:
            company_data["company"]["founded_year"] = int(founded)
        except:
            pass

    return company_data


def run_safety_check(company_data):
    """Run safety and validation checks"""
    print("\n" + "-" * 80)
    print("STEP 1: Safety Check & Validation")
    print("-" * 80)

    company = company_data.get("company", {})

    # Basic validation
    checks = {
        "Name provided": bool(company.get("name")),
        "Description length": len(company.get("description", "")) >= 20,
        "Has domains": len(company.get("domains", [])) > 0,
        "Country specified": bool(company.get("country")),
    }

    all_passed = all(checks.values())

    for check, passed in checks.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {check}: {status}")

    if not all_passed:
        print("\nERROR: Validation failed. Please check your input.")
        return False

    print("\n  All checks passed!")
    return True


def run_planner(company_data, iteration=1, previous_feedback=None):
    """Run SmartPlanner"""
    print(f"\n{'-' * 80}")
    print(f"STEP 2.{iteration}: Smart Planner (Iteration {iteration})")
    print("-" * 80)

    if previous_feedback:
        print(f"  Applying feedback: {previous_feedback[:80]}...")

    # Load SmartPlanner
    spec = importlib.util.spec_from_file_location(
        "smart_planner", "3_planning/smart_planner.py"
    )
    planner_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(planner_module)

    create_smart_plan = planner_module.create_smart_plan
    plan = create_smart_plan(company_data, previous_feedback=previous_feedback)

    print(f"\n  Analysis:")
    analysis = plan.get("analysis", {})
    print(f"    Technologies: {', '.join(analysis.get('technologies', [])[:5])}")
    print(f"    Applications: {', '.join(analysis.get('applications', [])[:3])}")
    print(f"    Target Programs: {', '.join(plan.get('target_programs', []))}")
    print(f"    Estimated Calls: {plan.get('estimated_calls')}")

    print(f"\n  Generated {len(plan['search_queries'])} search queries:")
    for i, query in enumerate(plan["search_queries"], 1):
        print(f"    {i}. {query}")

    return plan


def run_retrieval(plan, max_topics=3):
    """Run scraper/retrieval"""
    print("\n" + "-" * 80)
    print("STEP 3: Retrieving EU Funding Calls")
    print("-" * 80)
    print(f"  Searching with {len(plan['search_queries'])} queries...")
    print(f"  (This may take 1-2 minutes for detailed scraping)\n")

    spec = importlib.util.spec_from_file_location(
        "scraper_manager", "4_retrieval/scraper_manager.py"
    )
    scraper_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scraper_module)

    start_time = datetime.now()

    topics = scraper_module.scrape_topics_to_json(
        search_terms=plan["search_queries"],
        search_query=plan["filter_config"],
        headless=True,
        max_topics=max_topics,
    )

    elapsed = (datetime.now() - start_time).total_seconds()

    print(f"  Retrieved {len(topics)} topics in {elapsed:.1f} seconds\n")

    if topics:
        print("  Found calls:")
        for i, topic in enumerate(topics, 1):
            print(f"    {i}. {topic['id']}")
            print(f"       {topic['title'][:70]}...")
            print(f"       Programme: {topic['general_info']['programme']}")
            print(f"       Deadline: {topic['general_info']['dates']['deadline']}")

    return topics


def run_analysis(topics, company_data, iteration=1):
    """Run complete analysis on retrieved topics with all modules"""
    print("\n" + "-" * 80)
    print(f"STEP 4: Analyzing Calls (Iteration {iteration})")
    print("-" * 80)
    print("  Modules: Scorer + Eligibility + LLM Critic + Reflection")

    if not topics:
        print("  No topics to analyze")
        return [], "No topics found. Try broader search terms."

    # Load all analysis modules
    spec1 = importlib.util.spec_from_file_location("scorer", "5_analysis/scorer.py")
    scorer_module = importlib.util.module_from_spec(spec1)
    spec1.loader.exec_module(scorer_module)

    spec2 = importlib.util.spec_from_file_location(
        "eligibility", "5_analysis/eligibility.py"
    )
    eligibility_module = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(eligibility_module)

    spec3 = importlib.util.spec_from_file_location(
        "llm_critic", "5_analysis/llm_critic.py"
    )
    llm_critic_module = importlib.util.module_from_spec(spec3)
    spec3.loader.exec_module(llm_critic_module)

    spec4 = importlib.util.spec_from_file_location(
        "reflection", "5_analysis/reflection.py"
    )
    reflection_module = importlib.util.module_from_spec(spec4)
    spec4.loader.exec_module(reflection_module)

    company_profile = company_data.get("company", {})
    analyzed = []

    print(f"\n  Analyzing {len(topics)} calls with full analysis suite...\n")

    for i, topic in enumerate(topics, 1):
        print(f"  [{i}/{len(topics)}] {topic['title'][:50]}...")

        # 1. Eligibility Check
        eligibility = eligibility_module.apply_eligibility_filters(
            topic, company_profile
        )

        # 2. Quantitative Scoring
        scoring = scorer_module.score_call(topic, company_profile, {})

        # 3. Qualitative Analysis (LLM Critic)
        qualitative = llm_critic_module.perform_qualitative_analysis(
            topic, company_profile
        )

        analyzed.append(
            {
                "id": topic["id"],
                "title": topic["title"],
                "programme": topic["general_info"]["programme"],
                "deadline": topic["general_info"]["dates"]["deadline"],
                "score": scoring["total"],
                "score_breakdown": {
                    "domain_match": scoring.get("domain_match", 0),
                    "keyword_match": scoring.get("keyword_match", 0),
                    "eligibility_fit": scoring.get("eligibility_fit", 0),
                    "budget_feasibility": scoring.get("budget_feasibility", 0),
                },
                "eligible": eligibility["all_passed"],
                "eligibility_details": eligibility,
                "url": topic["url"],
                "match_summary": qualitative.get("match_summary", "N/A")[:100],
                "keyword_hits": qualitative.get("keyword_hits", []),
                "suggested_partners": qualitative.get("suggested_partners", []),
                "estimated_effort": qualitative.get("estimated_effort_hours", "N/A"),
                "analysis_method": qualitative.get("analysis_method", "rule_based"),
            }
        )

        print(f"       Score: {scoring['total']}/10")
        print(f"       Eligible: {'Yes' if eligibility['all_passed'] else 'No'}")
        print(f"       Match: {qualitative.get('match_summary', 'N/A')[:60]}...")
        if qualitative.get("keyword_hits"):
            print(f"       Keywords: {', '.join(qualitative['keyword_hits'][:3])}")

    # 4. Reflection - Decide next action
    print("\n  Running Reflection module...")
    search_params = {"max_results": 10, "portals": ["ftop", "eufunds_bg"]}
    reflection = reflection_module.reflect_on_results(
        analyzed, search_params, iteration
    )

    print(f"    Decision: {reflection['decision'].upper()}")
    print(f"    Reasoning: {reflection['reasoning']}")
    print(
        f"    Stats: {reflection['stats']['high_scores']} high, {reflection['stats']['medium_scores']} medium, {reflection['stats']['low_scores']} low"
    )

    # Generate feedback based on reflection
    feedback = None
    if reflection["decision"] == "refine":
        feedback = "; ".join(reflection["recommendations"])
        print(f"    Feedback: {feedback[:80]}...")
    elif reflection["decision"] == "finalize":
        print("    Status: Results are good - finalizing")

    return analyzed, feedback


def run_reporter(analyzed_calls):
    """Generate final report"""
    print("\n" + "=" * 80)
    print("FINAL REPORT")
    print("=" * 80)

    if not analyzed_calls:
        print("\nNo matching calls found.")
        return

    high_relevance = [c for c in analyzed_calls if c["score"] >= 7]
    eligible = [c for c in analyzed_calls if c["eligible"]]

    print(f"\nTotal calls analyzed: {len(analyzed_calls)}")
    print(f"High relevance (7+): {len(high_relevance)}")
    print(f"Eligible calls: {len(eligible)}")

    print("\n" + "-" * 80)
    print("TOP RECOMMENDATIONS:")
    print("-" * 80)

    # Sort by score
    sorted_calls = sorted(analyzed_calls, key=lambda x: x["score"], reverse=True)

    for i, call in enumerate(sorted_calls[:5], 1):
        print(f"\n{i}. {call['title']}")
        print(f"   ID: {call['id']}")
        print(f"   Programme: {call['programme']}")
        print(f"   Deadline: {call['deadline']}")
        print(f"   Relevance Score: {call['score']}/10")
        print(
            f"     - Domain Match: {call.get('score_breakdown', {}).get('domain_match', 0)}/10"
        )
        print(
            f"     - Keyword Match: {call.get('score_breakdown', {}).get('keyword_match', 0)}/10"
        )
        print(
            f"     - Budget Fit: {call.get('score_breakdown', {}).get('budget_feasibility', 0)}/10"
        )
        print(f"   Eligible: {'Yes' if call['eligible'] else 'No'}")
        print(f"   Match Summary: {call.get('match_summary', 'N/A')}")
        if call.get("keyword_hits"):
            print(f"   Matching Keywords: {', '.join(call['keyword_hits'][:5])}")
        if call.get("suggested_partners"):
            print(f"   Suggested Partners: {', '.join(call['suggested_partners'][:3])}")
        print(f"   Est. Effort: {call.get('estimated_effort', 'N/A')} hours")
        print(f"   URL: {call['url']}")

    # Save report to file
    report_file = f"eu_calls_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "timestamp": datetime.now().isoformat(),
                "total_calls": len(analyzed_calls),
                "high_relevance": len(high_relevance),
                "eligible_calls": len(eligible),
                "calls": sorted_calls,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )

    print(f"\n\nFull report saved to: {report_file}")


def main():
    try:
        print("=" * 80)
        print("EU CALL FINDER - COMPLETE WORKFLOW")
        print("=" * 80)

        # Get company input
        company_data = get_company_input_interactive()

        # Step 1: Safety Check
        if not run_safety_check(company_data):
            return

        # Step 2: Planner (Iteration 1)
        plan1 = run_planner(company_data, iteration=1)

        # Step 3: Retrieval
        topics = run_retrieval(plan1, max_topics=3)

        # Step 4: Analysis (Iteration 1)
        analyzed, feedback = run_analysis(topics, company_data, iteration=1)

        # Check if we need iteration 2
        if feedback:
            print(f"\n  Feedback from Reflection: {feedback}")
            response = (
                input("\nRun refined search with iteration 2? (y/n): ").strip().lower()
            )

            if response == "y":
                # Iteration 2
                plan2 = run_planner(
                    company_data, iteration=2, previous_feedback=feedback
                )
                topics2 = run_retrieval(plan2, max_topics=2)
                analyzed2, _ = run_analysis(topics2, company_data, iteration=2)

                # Combine results
                all_ids = {a["id"] for a in analyzed}
                for a in analyzed2:
                    if a["id"] not in all_ids:
                        analyzed.append(a)

        # Step 5: Reporter
        run_reporter(analyzed)

        print("\n" + "=" * 80)
        print("WORKFLOW COMPLETE!")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n\nWorkflow interrupted by user.")
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
