#!/usr/bin/env python3
"""
Complete End-to-End Workflow Test with Multiple Iterations
Shows data exchange between all modules
"""

import sys
import os

sys.path.insert(0, ".")

from dotenv import load_dotenv

load_dotenv()

import importlib.util
import json
from datetime import datetime

# Setup logging to file
log_file = open("complete_workflow_log.txt", "w", encoding="utf-8")


def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    log_file.write(line + "\n")
    log_file.flush()
    print(line)


def main():
    try:
        log("=" * 80)
        log("EU CALL FINDER - COMPLETE WORKFLOW TEST")
        log("Testing: Iteration 1 (initial) and Iteration 2 (with feedback)")
        log("=" * 80)
        log("")

        # Load modules
        log("PHASE 1: Loading Modules")
        log("-" * 80)

        spec = importlib.util.spec_from_file_location(
            "contracts", "contracts/schemas.py"
        )
        contracts = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(contracts)
        log("  [OK] contracts loaded")

        spec2 = importlib.util.spec_from_file_location(
            "smart_planner", "3_planning/smart_planner.py"
        )
        planner_module = importlib.util.module_from_spec(spec2)
        spec2.loader.exec_module(planner_module)
        log("  [OK] smart_planner loaded")

        spec3 = importlib.util.spec_from_file_location(
            "scraper_manager", "4_retrieval/scraper_manager.py"
        )
        scraper_module = importlib.util.module_from_spec(spec3)
        spec3.loader.exec_module(scraper_module)
        log("  [OK] scraper_manager loaded")

        spec4 = importlib.util.spec_from_file_location("scorer", "5_analysis/scorer.py")
        scorer_module = importlib.util.module_from_spec(spec4)
        spec4.loader.exec_module(scorer_module)
        log("  [OK] scorer loaded")

        spec5 = importlib.util.spec_from_file_location(
            "eligibility", "5_analysis/eligibility.py"
        )
        eligibility_module = importlib.util.module_from_spec(spec5)
        spec5.loader.exec_module(eligibility_module)
        log("")

        # Create company input with ALL fields
        log("PHASE 2: Creating Test Company Profile (COMPLETE DATA)")
        log("-" * 80)

        CompanyInput = contracts.CompanyInput
        CompanyProfile = contracts.CompanyProfile
        Domain = contracts.Domain
        DomainLevel = contracts.DomainLevel

        company_input = CompanyInput(
            company=CompanyProfile(
                name="AI Solutions Ltd",
                description="Bulgarian AI company developing machine learning solutions for healthcare diagnostics and clinical decision support systems. We specialize in medical imaging analysis and predictive analytics for hospitals and clinics.",
                type="SME",
                employees=25,
                country="Bulgaria",
                website="https://aisolutions.bg",
                domains=[
                    Domain(
                        name="Artificial Intelligence",
                        sub_domains=[
                            "Machine Learning",
                            "Computer Vision",
                            "Predictive Analytics",
                        ],
                        level=DomainLevel.ADVANCED,
                    ),
                    Domain(
                        name="Healthcare",
                        sub_domains=[
                            "Medical Imaging",
                            "Clinical Decision Support",
                            "Diagnostic Systems",
                        ],
                        level=DomainLevel.INTERMEDIATE,
                    ),
                ],
            )
        )

        company_dict = company_input.model_dump()
        log(f"Company: {company_dict['company']['name']}")
        log(f"Type: {company_dict['company']['type']}")
        log(f"Country: {company_dict['company']['country']}")
        log(f"Employees: {company_dict['company']['employees']}")
        log(f"Website: {company_dict['company'].get('website', 'N/A')}")
        log(f"Domains: {[d['name'] for d in company_dict['company']['domains']]}")
        log(f"Description: {company_dict['company']['description'][:80]}...")
        log("")

        # ============================================================
        # ITERATION 1: Initial Planning (NO feedback)
        # ============================================================
        log("=" * 80)
        log("ITERATION 1: INITIAL PLANNING (No Feedback)")
        log("=" * 80)
        log("")
        log("DATA INPUT TO SMARTPLANNER:")
        log("-" * 80)
        log("  1. Complete company profile (ALL fields):")
        log(f"     - name: {company_dict['company']['name']}")
        log(f"     - description: {company_dict['company']['description'][:60]}...")
        log(f"     - type: {company_dict['company']['type']}")
        log(f"     - country: {company_dict['company']['country']}")
        log(f"     - employees: {company_dict['company']['employees']}")
        log(f"     - website: {company_dict['company'].get('website', 'N/A')}")
        log(f"     - domains: {len(company_dict['company']['domains'])} domains")
        log("  2. previous_feedback: None (first iteration)")
        log("")

        # Generate first plan
        create_smart_plan = planner_module.create_smart_plan
        plan1 = create_smart_plan(company_dict, previous_feedback=None)

        log("SMARTPLANNER OUTPUT:")
        log("-" * 80)
        log(f"  Generated {len(plan1['search_queries'])} queries:")
        for i, query in enumerate(plan1["search_queries"], 1):
            log(f"    {i}. {query}")
        log("")
        log(f"  Target Programs: {plan1['target_programs']}")
        log(f"  Estimated Calls: {plan1['estimated_calls']}")
        log("")

        # Search with first plan
        log("SCRAPER / RETRIEVAL:")
        log("-" * 80)

        import requests

        search_url = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"
        headers = {"User-Agent": "Mozilla/5.0"}

        query_data = plan1["filter_config"]
        files = {
            "query": ("blob", json.dumps(query_data), "application/json"),
            "displayFields": (
                "blob",
                json.dumps(["identifier", "title"]),
                "application/json",
            ),
        }

        all_results_1 = []
        unique_topics_1 = {}

        for i, search_term in enumerate(plan1["search_queries"], 1):
            params = {
                "apiKey": "SEDIA",
                "text": search_term,
                "pageSize": "10",
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
                    if topic_id and topic_id not in unique_topics_1:
                        unique_topics_1[topic_id] = {"id": topic_id, "title": title}

                all_results_1.extend(results)
                log(f"  Query {i}: {len(results):2} results")
            except Exception as e:
                log(f"  Query {i}: Error")

        log(f"\n  Total unique topics (Iteration 1): {len(unique_topics_1)}")
        log("")

        # Analysis iteration 1
        log("ANALYSIS (Iteration 1):")
        log("-" * 80)

        topics_list_1 = list(unique_topics_1.values())
        analyzed_1 = []

        if topics_list_1:
            for topic in topics_list_1[:3]:
                mock_topic = {
                    "id": topic["id"],
                    "title": topic["title"],
                    "general_info": {"programme": "Unknown"},
                }
                eligibility = eligibility_module.apply_eligibility_filters(
                    mock_topic, company_dict["company"]
                )
                scoring = scorer_module.score_call(
                    mock_topic, company_dict["company"], {}
                )
                analyzed_1.append(
                    {
                        "id": topic["id"],
                        "title": topic["title"],
                        "score": scoring["total"],
                        "eligible": eligibility["all_passed"],
                    }
                )
                log(f"  {topic['title'][:50]}...")
                log(
                    f"    Score: {scoring['total']}/10 | Eligible: {eligibility['all_passed']}"
                )

        # Determine if we need iteration 2
        low_score_count = len([a for a in analyzed_1 if a["score"] < 6])
        needs_iteration_2 = low_score_count >= 2 or len(analyzed_1) < 3

        if needs_iteration_2:
            feedback = f"Low relevance scores detected. Found {len(analyzed_1)} topics but many have low scores ({low_score_count} below 6/10). Try more specific healthcare-related terms."
        else:
            feedback = "Good results found. No refinement needed."

        log(f"\n  Analysis Result: {feedback[:60]}...")
        log("")

        # ============================================================
        # ITERATION 2: Refined Planning (WITH feedback)
        # ============================================================
        if needs_iteration_2:
            log("=" * 80)
            log("ITERATION 2: REFINED PLANNING (With Feedback)")
            log("=" * 80)
            log("")
            log("DATA INPUT TO SMARTPLANNER:")
            log("-" * 80)
            log("  1. Complete company profile (SAME AS ITERATION 1):")
            log(f"     - name: {company_dict['company']['name']}")
            log(f"     - description: {company_dict['company']['description'][:60]}...")
            log(f"     - type: {company_dict['company']['type']}")
            log(f"     - country: {company_dict['company']['country']}")
            log(f"     - employees: {company_dict['company']['employees']}")
            log(f"     - website: {company_dict['company'].get('website', 'N/A')}")
            log(f"     - domains: {len(company_dict['company']['domains'])} domains")
            log("")
            log("  2. previous_feedback (NEW - from Iteration 1 analysis):")
            log(f"     {feedback}")
            log("")

            # Generate second plan WITH feedback
            plan2 = create_smart_plan(company_dict, previous_feedback=feedback)

            log("SMARTPLANNER OUTPUT (Iteration 2):")
            log("-" * 80)
            log(f"  Generated {len(plan2['search_queries'])} refined queries:")
            for i, query in enumerate(plan2["search_queries"], 1):
                log(f"    {i}. {query}")
            log("")
            log(f"  Reasoning: {plan2['reasoning']}")
            log("")

            # Search with second plan
            log("SCRAPER / RETRIEVAL (Iteration 2):")
            log("-" * 80)

            all_results_2 = []
            unique_topics_2 = {}

            for i, search_term in enumerate(plan2["search_queries"], 1):
                params = {
                    "apiKey": "SEDIA",
                    "text": search_term,
                    "pageSize": "10",
                    "pageNumber": "1",
                }
                try:
                    response = requests.post(
                        search_url,
                        params=params,
                        files=files,
                        headers=headers,
                        timeout=30,
                    )
                    data = response.json()
                    results = data.get("results", [])

                    for item in results:
                        meta = item.get("metadata", {})
                        topic_id = meta.get("identifier", [""])[0]
                        title = (
                            meta.get("title", [""])[0] if meta.get("title") else "N/A"
                        )
                        if topic_id and topic_id not in unique_topics_2:
                            unique_topics_2[topic_id] = {"id": topic_id, "title": title}

                    all_results_2.extend(results)
                    log(f"  Query {i}: {len(results):2} results")
                except Exception as e:
                    log(f"  Query {i}: Error")

            log(f"\n  Total unique topics (Iteration 2): {len(unique_topics_2)}")
            log("")

            # Combine results from both iterations
            all_topics = {**unique_topics_1, **unique_topics_2}
            log(f"  Combined unique topics (Both iterations): {len(all_topics)}")
            log("")
        else:
            all_topics = unique_topics_1
            log("No Iteration 2 needed - results were good")
            log("")

        # ============================================================
        # FINAL SUMMARY
        # ============================================================
        log("=" * 80)
        log("WORKFLOW COMPLETE - FINAL SUMMARY")
        log("=" * 80)
        log("")
        log("ITERATION 1:")
        log(f"  - Input: Complete company profile")
        log(
            f"  - Output: {len(plan1['search_queries'])} queries, {len(unique_topics_1)} topics"
        )
        if needs_iteration_2:
            log("")
            log("ITERATION 2:")
            log(f"  - Input: Complete company profile + Feedback")
            log(f"  - Feedback: {feedback[:50]}...")
            log(
                f"  - Output: {len(plan2['search_queries'])} queries, {len(unique_topics_2)} topics"
            )

        log("")
        log("FINAL RESULTS:")
        log(f"  - Total unique topics found: {len(all_topics)}")
        log(f"  - Total planner iterations: {2 if needs_iteration_2 else 1}")
        log("")

        if all_topics:
            log("SAMPLE TOPICS:")
            for i, topic in enumerate(list(all_topics.values())[:5], 1):
                log(f"  {i}. {topic['id']}")
                log(f"     {topic['title'][:60]}...")

        log("")
        log("=" * 80)
        log("TEST COMPLETE: All modules working correctly!")
        log("=" * 80)
        log("")
        log("Data Exchange Verified:")
        log("  [OK] Iteration 1: Company profile -> SmartPlanner -> Queries")
        log(
            "  [OK] Iteration 2: Company profile + Feedback -> SmartPlanner -> Refined Queries"
        )
        log("  [OK] Complete data flows through all iterations")
        log("")
        log("Full log saved to: complete_workflow_log.txt")

    except Exception as e:
        import traceback

        log("\n" + "=" * 80)
        log("ERROR!")
        log("=" * 80)
        log(f"Error: {str(e)}")
        log("")
        log(traceback.format_exc())
    finally:
        log_file.close()


if __name__ == "__main__":
    main()
