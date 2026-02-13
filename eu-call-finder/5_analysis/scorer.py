from typing import Dict, Optional


def score_call(
    call_data: dict, company_profile: dict, llm_insights: Optional[dict] = None
) -> dict:
    """
    Score a call based on 6 criteria with weighted scoring (1-10 scale).

    If llm_insights provided (LLM-first approach), uses LLM analysis for:
    - Domain Match (30%)
    - Keyword Match (15%)
    - Strategic Value (10%)

    Otherwise falls back to rule-based scoring.

    Weights: Domain Match (30%), Keyword Match (15%), Eligibility (20%),
             Budget (15%), Strategic Value (10%), Deadline (10%)
    """

    # Check if we have LLM insights (LLM-first approach)
    use_llm = llm_insights is not None and llm_insights.get("analysis_method") == "llm"

    if use_llm and llm_insights is not None:
        # Use LLM insights for nuanced scoring
        domain_score = _score_domain_match_from_llm(llm_insights)
        keyword_score = _score_keyword_match_from_llm(llm_insights)
        strategic_score = _score_strategic_value_from_llm(
            call_data, company_profile, llm_insights
        )

        # Apply LLM confidence boost
        confidence = llm_insights.get("llm_confidence", "medium")
        confidence_multiplier = {"high": 1.0, "medium": 0.95, "low": 0.90}.get(
            confidence, 0.95
        )
        domain_score = min(10.0, domain_score * confidence_multiplier)
        keyword_score = min(10.0, keyword_score * confidence_multiplier)
    else:
        # Fall back to rule-based scoring
        domain_score = _score_domain_match(call_data, company_profile)
        keyword_score = _score_keyword_match(call_data, company_profile)
        strategic_score = _score_strategic_value(call_data, company_profile)

    # These are always rule-based (hard constraints)
    eligibility_score = _score_eligibility(call_data, company_profile)
    budget_score = _score_budget_feasibility(call_data, company_profile)
    deadline_score = _score_deadline_comfort(call_data)

    # Calculate weighted total
    total = round(
        domain_score * 0.30
        + keyword_score * 0.15
        + eligibility_score * 0.20
        + budget_score * 0.15
        + strategic_score * 0.10
        + deadline_score * 0.10,
        1,
    )

    result = {
        "total": total,
        "domain_match": domain_score,
        "keyword_match": keyword_score,
        "eligibility_fit": eligibility_score,
        "budget_feasibility": budget_score,
        "strategic_value": strategic_score,
        "deadline_comfort": deadline_score,
        "recommendation": _get_recommendation(total),
        "scoring_method": "llm_enhanced" if use_llm else "rule_based",
    }

    # Include LLM reasoning if available
    if use_llm and llm_insights is not None and "llm_reasoning" in llm_insights:
        result["llm_reasoning"] = llm_insights["llm_reasoning"]

    return result


# LLM-BASED SCORING FUNCTIONS


def _score_domain_match_from_llm(llm_insights: dict) -> float:
    """Extract domain match score from LLM analysis."""
    domain_matches = llm_insights.get("domain_matches", [])

    if not domain_matches:
        return 3.0  # Neutral if no domain info

    # Count match strengths
    strong = sum(1 for m in domain_matches if m.get("strength") == "strong")
    moderate = sum(1 for m in domain_matches if m.get("strength") == "moderate")
    weak = sum(1 for m in domain_matches if m.get("strength") == "weak")

    # Calculate weighted score
    score = (strong * 9.0 + moderate * 6.5 + weak * 4.0) / max(len(domain_matches), 1)

    # Boost for multiple strong matches
    if strong >= 2:
        score = min(10.0, score + 1.0)

    return min(10.0, max(1.0, round(score, 1)))


def _score_keyword_match_from_llm(llm_insights: dict) -> float:
    """Extract keyword match score from LLM analysis."""
    keyword_hits = llm_insights.get("keyword_hits", [])
    match_summary = llm_insights.get("match_summary", "").lower()

    hit_count = len(keyword_hits)

    # Base score on hit count
    if hit_count >= 6:
        score = 9.5
    elif hit_count >= 4:
        score = 8.5
    elif hit_count >= 3:
        score = 7.0
    elif hit_count == 2:
        score = 5.5
    elif hit_count == 1:
        score = 4.0
    else:
        score = 2.5

    # Boost for excellence indicators in summary
    excellence_words = ["excellent", "perfect", "outstanding", "ideal"]
    if any(word in match_summary for word in excellence_words):
        score = min(10.0, score + 0.5)

    return score


def _score_strategic_value_from_llm(
    call_data: dict, company_profile: dict, llm_insights: dict
) -> float:
    """Extract strategic value from LLM insights and past projects."""
    relevant_projects = llm_insights.get("relevant_past_projects", [])

    if not relevant_projects:
        # Fall back to rule-based
        return _score_strategic_value(call_data, company_profile)

    # Score based on project relevance
    high_relevance = sum(1 for p in relevant_projects if p.get("relevance") == "high")
    medium_relevance = sum(
        1 for p in relevant_projects if p.get("relevance") == "medium"
    )

    score = high_relevance * 3.0 + medium_relevance * 1.5

    # Normalize to 1-10 scale
    if score >= 6:
        return 9.0
    elif score >= 4:
        return 8.0
    elif score >= 2:
        return 7.0
    else:
        return 6.0


# RULE-BASED SCORING FUNCTIONS (Fallback)


def _score_domain_match(call_data: dict, company_profile: dict) -> float:
    """Score based on domain overlap with expertise level and subdomain bonus."""
    company_domains = company_profile.get("domains", [])
    call_domains = call_data.get("required_domains", [])

    if not company_domains or not call_domains:
        return 3.0  # Neutral score instead of 1.0

    matches = []

    for cd in company_domains:
        cd_name = cd["name"].lower()
        cd_subs = [s.lower() for s in cd.get("sub_domains", [])]
        cd_level = cd.get("level", "basic")

        for rd in call_domains:
            rd_lower = rd.lower()
            match_score = 0

            # Direct domain name match
            if cd_name in rd_lower or rd_lower in cd_name:
                match_score = (
                    8.0
                    if cd_level in ["expert"]
                    else 7.0
                    if cd_level == "advanced"
                    else 5.5
                )
            else:
                # Check subdomain matches
                for sub in cd_subs:
                    if sub in rd_lower:
                        match_score = max(
                            match_score,
                            6.5 if cd_level in ["expert", "advanced"] else 4.5,
                        )
                        break

            if match_score > 0:
                matches.append(match_score)

    if not matches:
        return 2.0  # Low but not 1.0

    # Take top 2 matches and average
    matches.sort(reverse=True)
    top_matches = matches[:2]
    avg_score = sum(top_matches) / len(top_matches)

    # Bonus for multiple strong matches
    if len([m for m in matches if m >= 7.0]) >= 2:
        avg_score = min(10.0, avg_score + 1.0)

    return min(10.0, round(avg_score, 1))


def _score_keyword_match(call_data: dict, company_profile: dict) -> float:
    """Score based on keyword matching between company and call."""
    company_keywords = company_profile.get("keywords", {}).get("include", [])
    call_text = ""

    # Build call text from various fields
    content = call_data.get("content", {})
    call_text += content.get("description", "") + " "
    call_text += call_data.get("title", "") + " "
    call_text += " ".join(call_data.get("keywords", []))

    call_text_lower = call_text.lower()

    if not company_keywords:
        return 5.0  # Neutral if no keywords defined

    matches = 0
    total_keywords = len(company_keywords)

    for keyword in company_keywords:
        keyword_lower = keyword.lower()
        # Check exact match
        if keyword_lower in call_text_lower:
            matches += 1
        else:
            # Check expanded variations
            variations = _expand_keyword(keyword_lower)
            if any(var in call_text_lower for var in variations):
                matches += 0.8  # Slightly lower score for variation match

    # Calculate score based on match ratio
    match_ratio = matches / total_keywords if total_keywords > 0 else 0

    if match_ratio >= 0.7:
        return 9.5
    elif match_ratio >= 0.5:
        return 8.0
    elif match_ratio >= 0.3:
        return 6.5
    elif match_ratio >= 0.1:
        return 4.5
    else:
        return 3.0


def _expand_keyword(keyword: str) -> set:
    """Get semantic equivalents and variations for a keyword."""
    keyword = keyword.lower().strip()

    # Semantic equivalence map
    equivalents = {
        # AI variations
        "ai": {
            "ai",
            "artificial intelligence",
            "machine intelligence",
            "cognitive computing",
        },
        "artificial intelligence": {
            "ai",
            "artificial intelligence",
            "machine intelligence",
        },
        "machine learning": {
            "machine learning",
            "ml",
            "deep learning",
            "neural networks",
            "predictive modeling",
        },
        "ml": {"machine learning", "ml", "deep learning"},
        "deep learning": {"deep learning", "neural networks", "ml", "machine learning"},
        "nlp": {
            "nlp",
            "natural language processing",
            "text analysis",
            "language understanding",
            "computational linguistics",
        },
        "natural language processing": {
            "nlp",
            "natural language processing",
            "text analysis",
        },
        "llm": {
            "llm",
            "large language model",
            "foundation model",
            "generative ai",
            "gpt",
        },
        "large language model": {"llm", "large language model", "foundation model"},
        "generative ai": {"generative ai", "gen ai", "ai generation"},
    }

    return equivalents.get(keyword, {keyword})


def _score_strategic_value(call_data: dict, company_profile: dict) -> float:
    """Score based on strategic alignment with company goals."""
    # Check past projects alignment
    past_projects = company_profile.get("past_eu_projects", [])
    call_program = call_data.get("general_info", {}).get("programme", "")

    if not past_projects:
        return 5.0  # Neutral

    # Check if company has worked in similar program
    program_matches = sum(
        1 for p in past_projects if call_program in p.get("program", "")
    )

    if program_matches >= 2:
        return 8.5
    elif program_matches == 1:
        return 7.0
    else:
        return 5.5


def _score_eligibility(call_data: dict, company_profile: dict) -> float:
    """Score eligibility fit (0-10, where 10 = fully eligible)."""
    # This is a simplified version - the real eligibility check is in eligibility.py
    score = 10.0

    # Check budget feasibility
    budget = call_data.get("budget_per_project", {})
    max_budget = budget.get("max", 0)

    # SME preference for smaller budgets
    if company_profile.get("type") == "SME":
        if max_budget > 5000000:
            score -= 1.5
        elif max_budget > 10000000:
            score -= 3.0

    return max(1.0, score)


def _score_budget_feasibility(call_data: dict, company_profile: dict) -> float:
    """Score budget feasibility for the company."""
    budget = call_data.get("budget_per_project", {})
    min_budget = budget.get("min", 0)
    max_budget = budget.get("max", 0)
    avg_budget = (
        (min_budget + max_budget) / 2 if min_budget and max_budget else max_budget
    )

    company_type = company_profile.get("type", "")
    employees = company_profile.get("employees", 50)

    # SME considerations
    if company_type == "SME":
        if avg_budget <= 500000:
            return 8.0
        elif avg_budget <= 1000000:
            return 7.0
        elif avg_budget <= 3000000:
            return 5.5
        elif avg_budget <= 5000000:
            return 4.0
        else:
            return 2.5
    else:
        # Larger organizations can handle bigger budgets
        if avg_budget <= 5000000:
            return 8.5
        elif avg_budget <= 10000000:
            return 7.5
        else:
            return 6.0


def _score_deadline_comfort(call_data: dict) -> float:
    """Score deadline comfort based on days remaining."""
    from datetime import datetime

    general_info = call_data.get("general_info", {})
    dates = general_info.get("dates", {})
    deadline_str = dates.get("deadline", "")

    if not deadline_str:
        return 5.0  # Neutral if no deadline info

    # Parse deadline
    import re

    date_match = re.search(
        r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
        deadline_str,
        re.IGNORECASE,
    )

    if not date_match:
        return 5.0

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
        return 5.0

    # Score based on days remaining
    if days_until < 0:
        return 1.0  # Already passed
    elif days_until < 14:
        return 3.0  # Very urgent
    elif days_until < 30:
        return 4.5  # Urgent
    elif days_until < 60:
        return 6.5  # Tight but doable
    elif days_until < 120:
        return 8.0  # Comfortable
    else:
        return 9.0  # Very comfortable


def _get_recommendation(total_score: float) -> dict:
    """Get recommendation based on total score."""
    if total_score >= 7.5:
        return {"action": "apply", "label": "КАНДИДАТСТВАЙТЕ", "color": "green"}
    elif total_score >= 5.5:
        return {"action": "consider", "label": "ОБМИСЛЕТЕ", "color": "yellow"}
    elif total_score >= 3.5:
        return {"action": "monitor", "label": "НАБЛЮДАВАЙТЕ", "color": "blue"}
    else:
        return {"action": "skip", "label": "ПРОПУСНЕТЕ", "color": "red"}
