#!/usr/bin/env python3
"""
Test runner for analysis logic.
Loads mock data, runs all analysis functions, and saves results.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import importlib.util

# Load modules from 5_analysis directory
analysis_dir = Path(__file__).parent.parent / "5_analysis"


def load_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


# Import analysis modules
scorer = load_module_from_path("scorer", analysis_dir / "scorer.py")
llm_critic = load_module_from_path("llm_critic", analysis_dir / "llm_critic.py")
eligibility = load_module_from_path("eligibility", analysis_dir / "eligibility.py")
reflection = load_module_from_path("reflection", analysis_dir / "reflection.py")

score_call = scorer.score_call
perform_qualitative_analysis = llm_critic.perform_qualitative_analysis
apply_eligibility_filters = eligibility.apply_eligibility_filters
reflect_on_results = reflection.reflect_on_results
evaluate_confidence = reflection.evaluate_confidence


def run_analysis_tests(mock_data_path: str, output_path: str):
    """
    Run all analysis functions on mock data and save results.
    """
    # Load mock data
    with open(mock_data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    company_profile = data["company_profile"]
    calls = data["calls"]

    # Store results
    results = []

    print(f"Running analysis on {len(calls)} mock calls...\n")

    for call in calls:
        call_id = call["id"]
        print(f"Analyzing: {call_id}")

        # Run scoring
        try:
            scoring_result = score_call(call, company_profile)
            print(f"  [OK] Score: {scoring_result['total']}/10")
        except Exception as e:
            print(f"  [ERR] Scoring error: {e}")
            scoring_result = {"error": str(e)}

        # Run qualitative analysis
        try:
            analysis_result = perform_qualitative_analysis(call, company_profile)
            print(f"  [OK] Qualitative analysis complete")
        except Exception as e:
            print(f"  [ERR] Analysis error: {e}")
            analysis_result = {"error": str(e)}

        # Run eligibility check
        try:
            eligibility_result = apply_eligibility_filters(call, company_profile)
            passed_checks = sum(
                [
                    eligibility_result.get("type_ok", False),
                    eligibility_result.get("country_ok", False),
                    eligibility_result.get("budget_ok", False),
                    eligibility_result.get("trl_ok", False),
                ]
            )
            status = (
                "PASS"
                if eligibility_result["all_passed"]
                else f"PARTIAL({passed_checks}/4)"
            )
            print(f"  [OK] Eligibility: {status}")
        except Exception as e:
            print(f"  [ERR] Eligibility error: {e}")
            eligibility_result = {"error": str(e)}

        # Combine results
        # Extract fields from new structure (matching real webscrape format)
        general_info = call.get("general_info", {})
        dates = general_info.get("dates", {})
        deadline_str = dates.get("deadline", "")

        # Calculate days until deadline
        days_until = 0
        if deadline_str:
            date_match = re.search(
                r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
                deadline_str,
                re.IGNORECASE,
            )
            if date_match:
                months = {
                    "january": 1,
                    "february": 2,
                    "march": 3,
                    "april": 4,
                    "may": 5,
                    "june": 6,
                    "july": 7,
                    "august": 8,
                    "september": 9,
                    "october": 10,
                    "november": 11,
                    "december": 12,
                }
                try:
                    deadline_date = datetime(
                        int(date_match.group(3)),
                        months[date_match.group(2).lower()],
                        int(date_match.group(1)),
                    )
                    days_until = (deadline_date - datetime.now()).days
                except:
                    days_until = 0

        result_entry = {
            "call_id": call_id,
            "title": call.get("title", ""),
            "portal": general_info.get("call", ""),  # Extract from general_info.call
            "program": general_info.get("programme", ""),
            "deadline": deadline_str,
            "days_until_deadline": days_until,
            "budget_per_project": call.get("budget_per_project", {}),
            "analysis": {
                "scoring": scoring_result,
                "qualitative": analysis_result,
                "eligibility": eligibility_result,
            },
        }

        results.append(result_entry)
        print()

    # Sort by score
    results.sort(key=lambda x: x["analysis"]["scoring"].get("total", 0), reverse=True)

    # Add rankings
    for i, result in enumerate(results, 1):
        result["rank"] = i

    # Run reflection on all results
    print("Running reflection analysis...")
    search_params = company_profile.get("search_params", {})

    # Prepare flattened results for reflection (expects specific fields for confidence check)
    flat_results = []
    for r in results:
        flat_results.append(
            {
                "score": r["analysis"]["scoring"].get("total", 0),
                "info": {
                    "portal": r.get("portal", ""),
                    "title": r.get("title", ""),
                    "deadline": r.get("deadline", ""),
                    "budget_per_project": r.get("budget_per_project", {}),
                },
                "analysis": {
                    "match_summary": r.get("analysis", {})
                    .get("qualitative", {})
                    .get("match_summary", "")
                },
                "scoring": {"total": r["analysis"]["scoring"].get("total", 0)},
            }
        )

    reflection_result = reflect_on_results(flat_results, search_params, iteration=1)
    confidence = evaluate_confidence(flat_results)

    # Compile final output
    output = {
        "metadata": {
            "test_run_at": datetime.now().isoformat(),
            "mock_data_file": mock_data_path,
            "total_calls_analyzed": len(calls),
            "company_name": company_profile["name"],
        },
        "summary": {
            "reflection": reflection_result,
            "confidence": confidence,
            "top_recommendation": results[0]["call_id"] if results else None,
            "highest_score": results[0]["analysis"]["scoring"].get("total", 0)
            if results
            else 0,
            "average_score": round(
                sum(r["analysis"]["scoring"].get("total", 0) for r in results)
                / len(results),
                2,
            )
            if results
            else 0,
        },
        "ranked_results": results,
    }

    # Save results
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Results saved to: {output_path}")
    print(f"\nSummary:")
    print(f"  - Analyzed: {len(calls)} calls")
    print(f"  - Highest score: {output['summary']['highest_score']}/10")
    print(f"  - Average score: {output['summary']['average_score']}/10")
    print(f"  - Confidence: {confidence['level']} ({confidence['score']}%)")
    print(f"  - Recommendation: {reflection_result['decision']}")


if __name__ == "__main__":
    mock_data_path = "eu-call-finder/mock_data/sample_calls.json"
    output_path = "eu-call-finder/mock_data/test_results.json"

    run_analysis_tests(mock_data_path, output_path)
