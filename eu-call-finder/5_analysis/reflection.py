def reflect_on_results(results: list, search_params: dict, iteration: int = 1) -> dict:
    """
    Decide if analysis results are sufficient or if we need more searching/refinement.
    Returns decision on whether to continue, expand, or finalize.
    """

    # Check basic result counts
    total_found = len(results)
    min_results = search_params.get("max_results", 30)

    # Calculate score distribution
    scores = [r.get("relevance_score", 0) for r in results]
    high_scores = [s for s in scores if s >= 8.0]
    medium_scores = [s for s in scores if 6.0 <= s < 8.0]
    low_scores = [s for s in scores if s < 5.0]

    avg_score = sum(scores) / len(scores) if scores else 0
    max_score = max(scores) if scores else 0

    # Determine if we have enough quality results
    sufficient_quality = len(high_scores) >= 2 or (
        len(high_scores) >= 1 and len(medium_scores) >= 3
    )
    sufficient_quantity = total_found >= min(min_results, 10)

    # Check coverage across portals
    portals_covered = set()
    for result in results:
        portal = result.get("info", {}).get("portal", "")
        if portal:
            portals_covered.add(portal)

    target_portals = set(search_params.get("portals", []))
    portal_coverage = (
        len(portals_covered) / len(target_portals) if target_portals else 1.0
    )

    # Decision logic
    decision = make_decision(
        iteration=iteration,
        total_found=total_found,
        min_results=min_results,
        high_count=len(high_scores),
        medium_count=len(medium_scores),
        low_count=len(low_scores),
        avg_score=avg_score,
        max_score=max_score,
        sufficient_quality=sufficient_quality,
        sufficient_quantity=sufficient_quantity,
        portal_coverage=portal_coverage,
    )

    return {
        "decision": decision["action"],
        "reasoning": decision["reasoning"],
        "recommendations": decision["recommendations"],
        "stats": {
            "total_results": total_found,
            "high_scores": len(high_scores),
            "medium_scores": len(medium_scores),
            "low_scores": len(low_scores),
            "average_score": round(avg_score, 2),
            "max_score": max_score,
            "portals_covered": list(portals_covered),
            "portal_coverage": round(portal_coverage * 100, 1),
        },
    }


def make_decision(
    iteration: int,
    total_found: int,
    min_results: int,
    high_count: int,
    medium_count: int,
    low_count: int,
    avg_score: float,
    max_score: float,
    sufficient_quality: bool,
    sufficient_quantity: bool,
    portal_coverage: float,
) -> dict:
    """
    Make a decision on whether results are sufficient.

    Actions:
    - "finalize": Results are good enough, stop searching
    - "expand": Need more results, search additional portals
    - "refine": Results are poor, need to refine search criteria
    - "retry": Technical issues, should retry failed portals
    """

    # Too many iterations - must finalize
    if iteration >= 3:
        if total_found == 0:
            return {
                "action": "finalize",
                "reasoning": f"Maximum iterations ({iteration}) reached with no results. Finalizing empty.",
                "recommendations": [
                    "Consider broadening search criteria for future searches",
                    "Check if target portals have active calls",
                ],
            }
        else:
            return {
                "action": "finalize",
                "reasoning": f"Maximum iterations ({iteration}) reached. Using {total_found} results found.",
                "recommendations": [
                    f"Top result scored {max_score}/10",
                    f"Average score: {avg_score:.1f}/10",
                ],
            }

    # No results at all - expand search
    if total_found == 0:
        return {
            "action": "expand",
            "reasoning": "No results found in initial search. Need to expand to additional portals.",
            "recommendations": [
                "Search additional portals not in initial list",
                "Broaden keyword criteria",
                "Consider alternative search terms",
            ],
        }

    # Poor quality results - refine criteria
    if avg_score < 4.0 and total_found >= 5:
        return {
            "action": "refine",
            "reasoning": f"Found {total_found} results but average score is only {avg_score:.1f}/10. Criteria may be too broad.",
            "recommendations": [
                "Tighten domain requirements",
                "Add more specific keywords",
                "Increase minimum score threshold",
                "Focus on specific programs",
            ],
        }

    # Low coverage of target portals - expand
    if portal_coverage < 0.5 and iteration < 2:
        return {
            "action": "expand",
            "reasoning": f"Only {portal_coverage * 100:.0f}% of target portals returned results. Need to search remaining portals.",
            "recommendations": [
                "Retry failed portal connections",
                "Search remaining target portals",
                "Check for API rate limits",
            ],
        }

    # Good results but want more quantity
    if sufficient_quality and not sufficient_quantity and iteration < 2:
        return {
            "action": "expand",
            "reasoning": f"Good quality results ({high_count} high scores) but only {total_found} total. Can search for more.",
            "recommendations": [
                "Expand search to additional pages",
                "Search broader date ranges",
                "Include more programs",
            ],
        }

    # Excellent results - finalize
    if sufficient_quality and sufficient_quantity:
        return {
            "action": "finalize",
            "reasoning": f"Results are sufficient: {high_count} high-quality matches found with average score {avg_score:.1f}/10.",
            "recommendations": [
                f"Proceed with top {min(high_count, 5)} recommendations",
                "Prepare detailed analysis for high-scoring calls",
                "Consider setting up monitoring for similar future calls",
            ],
        }

    # Default - finalize with what we have
    return {
        "action": "finalize",
        "reasoning": f"Search completed with {total_found} results. Quality acceptable (avg: {avg_score:.1f}/10).",
        "recommendations": [
            f"Review {high_count} high-priority and {medium_count} medium-priority calls",
            "Consider manual review of borderline cases",
        ],
    }


def evaluate_confidence(results: list) -> dict:
    """
    Evaluate confidence level in the analysis results.
    """
    if not results:
        return {"level": "low", "score": 0.0, "reason": "No results to evaluate"}

    # Check data completeness
    completeness_scores = []
    for result in results:
        score = 0
        info = result.get("info", {})

        # Required fields
        if info.get("title"):
            score += 1
        if info.get("deadline"):
            score += 1
        if info.get("budget_per_project"):
            score += 1
        if result.get("analysis", {}).get("match_summary"):
            score += 1
        if result.get("scoring", {}).get("total"):
            score += 1

        completeness_scores.append(score / 5.0)

    avg_completeness = sum(completeness_scores) / len(completeness_scores)

    # Check consistency of scores
    scores = [r.get("relevance_score", 0) for r in results]
    if len(scores) > 1:
        variance = sum((s - (sum(scores) / len(scores))) ** 2 for s in scores) / len(
            scores
        )
        std_dev = variance**0.5
    else:
        std_dev = 0

    # Determine confidence
    if avg_completeness >= 0.9 and std_dev < 2.0:
        level = "high"
    elif avg_completeness >= 0.7 and std_dev < 3.0:
        level = "medium"
    else:
        level = "low"

    return {
        "level": level,
        "score": round(avg_completeness * 100, 1),
        "data_completeness": round(avg_completeness * 100, 1),
        "score_consistency": "consistent" if std_dev < 2.5 else "variable",
        "std_deviation": round(std_dev, 2),
    }
