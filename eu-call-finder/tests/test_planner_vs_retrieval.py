#!/usr/bin/env python3
"""
Test analysis with both Planner output and Retrieval data.
Shows how the critic validates if scraped calls match the planner's intent.
"""

import json
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
eligibility = load_module_from_path("eligibility", analysis_dir / "eligibility.py")

score_call = scorer.score_call
apply_eligibility_filters = eligibility.apply_eligibility_filters


def validate_against_planner(call_data: dict, planner_data: dict) -> dict:
    """
    Validate if a scraped call matches what the planner intended to find.
    """
    search_strategy = planner_data.get("search_strategy", {})
    target_criteria = planner_data.get("target_criteria", {})

    # Check 1: Domain alignment with planner priority
    planner_domains = set(
        d.lower() for d in search_strategy.get("priority_domains", [])
    )
    call_domains = set(d.lower() for d in call_data.get("required_domains", []))

    domain_match_score = 0
    matched_domains = []
    for cd in call_domains:
        for pd in planner_domains:
            if pd in cd or cd in pd:
                domain_match_score += 1
                matched_domains.append(cd)
                break

    # Check 2: Keyword alignment
    must_have = set(k.lower() for k in search_strategy.get("keywords_must_have", []))
    nice_to_have = set(
        k.lower() for k in search_strategy.get("keywords_nice_to_have", [])
    )
    call_keywords = set(k.lower() for k in call_data.get("keywords", []))

    must_have_hits = len(must_have & call_keywords)
    nice_to_have_hits = len(nice_to_have & call_keywords)

    # Check 3: Excluded sectors
    excluded = set(e.lower() for e in search_strategy.get("excluded_sectors", []))
    exclusion_violations = []
    for kw in call_keywords:
        for ex in excluded:
            if ex in kw:
                exclusion_violations.append(ex)

    # Check 4: Program alignment
    target_programs = [p.lower() for p in search_strategy.get("target_programs", [])]
    call_program = call_data.get("general_info", {}).get("programme", "").lower()
    program_match = any(tp in call_program for tp in target_programs)

    # Check 5: Deadline fit
    deadline_pref = target_criteria.get("deadline_preferences", {})
    days_until = calculate_days_until_deadline(call_data)

    deadline_fit = "unknown"
    if days_until > 0:
        if days_until < deadline_pref.get("minimum_days", 30):
            deadline_fit = "too_soon"
        elif days_until > deadline_pref.get("maximum_days", 365):
            deadline_fit = "too_far"
        else:
            deadline_fit = "good"

    return {
        "planner_intent_match": {
            "score": min(
                10, (domain_match_score * 3) + (must_have_hits * 2) + nice_to_have_hits
            ),
            "matched_priority_domains": matched_domains,
            "must_have_keywords_found": must_have_hits,
            "nice_to_have_keywords_found": nice_to_have_hits,
            "exclusion_violations": exclusion_violations,
            "program_alignment": program_match,
            "deadline_fit": deadline_fit,
            "days_until_deadline": days_until,
        },
        "alignment_summary": generate_alignment_summary(
            domain_match_score,
            must_have_hits,
            exclusion_violations,
            program_match,
            deadline_fit,
        ),
    }


def calculate_days_until_deadline(call_data: dict) -> int:
    """Calculate days until deadline from call data."""
    from datetime import datetime
    import re

    general_info = call_data.get("general_info", {})
    dates = general_info.get("dates", {})
    deadline_str = dates.get("deadline", "")

    if not deadline_str:
        return 0

    # Parse date
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
            return (deadline_date - datetime.now()).days
        except:
            pass

    return 0


def generate_alignment_summary(
    domain_matches, must_have, exclusions, program_match, deadline_fit
):
    """Generate human-readable summary of planner-retrieval alignment."""
    issues = []
    positives = []

    if domain_matches >= 2:
        positives.append(f"Strong domain alignment ({domain_matches} priority domains)")
    elif domain_matches == 1:
        positives.append("Partial domain alignment (1 priority domain)")
    else:
        issues.append("Weak domain alignment - doesn't match priority domains")

    if must_have >= 3:
        positives.append(f"Excellent keyword match ({must_have} must-have keywords)")
    elif must_have >= 1:
        positives.append(f"Good keyword match ({must_have} must-have keywords)")
    else:
        issues.append("Poor keyword alignment")

    if exclusions:
        issues.append(f"Contains excluded sectors: {', '.join(set(exclusions))}")

    if program_match:
        positives.append("Matches target programs")

    if deadline_fit == "too_soon":
        issues.append("Deadline too soon - may not have time to prepare")
    elif deadline_fit == "too_far":
        positives.append("Long-term opportunity - good for planning")
    elif deadline_fit == "good":
        positives.append("Deadline timing is ideal")

    if issues and positives:
        return f"Mixed alignment. Positives: {'; '.join(positives)}. Issues: {'; '.join(issues)}"
    elif issues:
        return f"Poor alignment. Issues: {'; '.join(issues)}"
    else:
        return f"Excellent alignment. {'; '.join(positives)}"


def run_planner_comparison_test():
    """Run analysis comparing planner intent vs retrieval reality."""

    # Load planner output
    planner_path = Path("eu-call-finder/mock_data/planner_output.json")
    with open(planner_path, "r", encoding="utf-8") as f:
        planner_data = json.load(f)

    # Load retrieval results
    retrieval_path = Path("eu-call-finder/mock_data/sample_calls_v2.json")
    with open(retrieval_path, "r", encoding="utf-8") as f:
        retrieval_data = json.load(f)

    company_profile = retrieval_data["company_profile"]
    calls = retrieval_data["calls"]

    print("=" * 80)
    print("PLANNER vs RETRIEVAL VALIDATION")
    print("=" * 80)
    print(f"\nPlanner Objective: {planner_data['search_strategy']['objective']}")
    print(
        f"Priority Domains: {', '.join(planner_data['search_strategy']['priority_domains'])}"
    )
    print(f"Expected Calls: {planner_data['expected_outcomes']['min_total_calls']}")
    print(f"Retrieved Calls: {len(calls)}")
    print("\n" + "=" * 80)

    results = []

    for i, call in enumerate(calls, 1):
        call_id = call["id"]
        print(f"\n{i}. Analyzing: {call_id}")

        # 1. Standard analysis
        scoring_result = score_call(call, company_profile)
        eligibility_result = apply_eligibility_filters(call, company_profile)

        # 2. Planner alignment check
        planner_validation = validate_against_planner(call, planner_data)

        # 3. Combined assessment
        combined_score = round(
            (scoring_result["total"] * 0.7)
            + (planner_validation["planner_intent_match"]["score"] * 0.3),
            1,
        )

        print(f"   Standard Score: {scoring_result['total']}/10")
        print(
            f"   Planner Alignment: {planner_validation['planner_intent_match']['score']}/10"
        )
        print(f"   Combined Score: {combined_score}/10")
        print(
            f"   Eligibility: {'PASS' if eligibility_result['all_passed'] else 'PARTIAL'}"
        )
        print(f"   Alignment: {planner_validation['alignment_summary'][:100]}...")

        result = {
            "call_id": call_id,
            "title": call.get("title", ""),
            "standard_score": scoring_result["total"],
            "planner_alignment_score": planner_validation["planner_intent_match"][
                "score"
            ],
            "combined_score": combined_score,
            "eligibility_passed": eligibility_result["all_passed"],
            "planner_validation": planner_validation,
            "analysis": scoring_result,
        }
        results.append(result)

    # Sort by combined score
    results.sort(key=lambda x: x["combined_score"], reverse=True)

    # Add rankings
    for i, r in enumerate(results, 1):
        r["rank"] = i

    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    avg_standard = round(sum(r["standard_score"] for r in results) / len(results), 2)
    avg_planner = round(
        sum(r["planner_alignment_score"] for r in results) / len(results), 2
    )
    avg_combined = round(sum(r["combined_score"] for r in results) / len(results), 2)

    high_alignment = len([r for r in results if r["planner_alignment_score"] >= 7])
    low_alignment = len([r for r in results if r["planner_alignment_score"] <= 3])

    print(f"\nAverage Standard Score: {avg_standard}/10")
    print(f"Average Planner Alignment: {avg_planner}/10")
    print(f"Average Combined Score: {avg_combined}/10")
    print(f"\nHigh Planner Alignment (7-10): {high_alignment} calls")
    print(f"Low Planner Alignment (0-3): {low_alignment} calls")

    # Top 3 recommendations
    print(f"\nTop 3 Recommendations:")
    for r in results[:3]:
        print(f"  {r['rank']}. {r['call_id']} - {r['combined_score']}/10")
        print(f"     Reason: {r['planner_validation']['alignment_summary'][:80]}...")

    # Save results
    output = {
        "metadata": {
            "test_run_at": datetime.now().isoformat(),
            "planner_file": str(planner_path),
            "retrieval_file": str(retrieval_path),
            "total_calls_analyzed": len(calls),
        },
        "summary": {
            "avg_standard_score": avg_standard,
            "avg_planner_alignment": avg_planner,
            "avg_combined_score": avg_combined,
            "high_alignment_count": high_alignment,
            "low_alignment_count": low_alignment,
            "top_recommendation": results[0]["call_id"] if results else None,
        },
        "planner_intent": {
            "objective": planner_data["search_strategy"]["objective"],
            "priority_domains": planner_data["search_strategy"]["priority_domains"],
            "expected_calls": planner_data["expected_outcomes"]["min_total_calls"],
            "actual_calls": len(calls),
        },
        "ranked_results": results,
    }

    output_path = Path("eu-call-finder/mock_data/planner_retrieval_analysis.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n[OK] Results saved to: {output_path}")


if __name__ == "__main__":
    run_planner_comparison_test()
