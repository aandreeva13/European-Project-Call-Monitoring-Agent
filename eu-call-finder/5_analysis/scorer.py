from __future__ import annotations

from typing import Optional


class ScoreQuality:
    """Data-quality diagnostics for a scored call.

    Note: this is intentionally a simple class (not a dataclass) because some
    scripts load this module via `importlib.util.module_from_spec()` without
    registering it in `sys.modules`, which can break `@dataclass` on Py3.12.
    """

    def __init__(self, level: str, score: float, reasons: list[str]):
        self.level = level  # high | medium | low
        self.score = score  # 0..100
        self.reasons = reasons


def score_call(
    call_data: dict, company_profile: dict, llm_insights: Optional[dict] = None
) -> dict:
    """Score a call based on 6 criteria with weighted scoring (1-10 scale).

    Weights: Domain Match (30%), Keyword Match (15%), Eligibility (20%),
             Budget (15%), Strategic Value (10%), Deadline (10%)

    Behavior:
    - If LLM insights are available (analysis_method == "llm"), use LLM-enhanced
      scoring for domain/keyword/strategic criteria.
    - Otherwise, fall back to deterministic rule-based scoring.

    Additionally:
    - Computes a data-quality indicator and applies a *small* penalty when the
      call content is too sparse (e.g., missing description/keywords/domains).
      This prevents inflated or misleading mid-scores caused by “unknown => neutral”.
    """

    use_llm = bool(llm_insights) and llm_insights.get("analysis_method") == "llm"

    if use_llm:
        # Use LLM insights for nuanced scoring
        domain_score = _score_domain_match_from_llm(llm_insights)
        keyword_score = _score_keyword_match_from_llm(llm_insights)
        strategic_score = _score_strategic_value_from_llm(
            call_data, company_profile, llm_insights
        )

        # Apply LLM confidence adjustment
        confidence = llm_insights.get("llm_confidence", "medium")
        confidence_multiplier = {"high": 1.0, "medium": 0.95, "low": 0.90}.get(
            confidence, 0.95
        )
        domain_score = min(10.0, domain_score * confidence_multiplier)
        keyword_score = min(10.0, keyword_score * confidence_multiplier)
        scoring_method = "llm_enhanced"
    else:
        # Rule-based fallback (no LLM configured or LLM failed)
        domain_score = _score_domain_match(call_data, company_profile)
        keyword_score = _score_keyword_match(call_data, company_profile)
        strategic_score = _score_strategic_value(call_data, company_profile)
        scoring_method = "rule_based"

    # These are always rule-based (hard constraints)
    eligibility_score = _score_eligibility(call_data, company_profile)
    budget_score = _score_budget_feasibility(call_data, company_profile)
    deadline_score = _score_deadline_comfort(call_data)

    # Calculate weighted total
    total_raw = (
        domain_score * 0.30
        + keyword_score * 0.15
        + eligibility_score * 0.20
        + budget_score * 0.15
        + strategic_score * 0.10
        + deadline_score * 0.10
    )

    quality = _assess_call_data_quality(call_data)
    total = round(_apply_quality_penalty(total_raw, quality), 1)

    result = {
        "total": total,
        "total_raw": round(total_raw, 1),
        "domain_match": round(domain_score, 1),
        "keyword_match": round(keyword_score, 1),
        "eligibility_fit": round(eligibility_score, 1),
        "budget_feasibility": round(budget_score, 1),
        "strategic_value": round(strategic_score, 1),
        "deadline_comfort": round(deadline_score, 1),
        "recommendation": _get_recommendation(total),
        "scoring_method": scoring_method,
        "data_quality": {
            "level": quality.level,
            "score": quality.score,
            "reasons": quality.reasons,
            "penalty_applied": round(total_raw - total, 2),
        },
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
    """Score eligibility fit (1-10).

    Important: eligibility fields are often missing in scraped data.
    This scorer is intentionally conservative when key fields are unknown.

    Note: hard eligibility gating still lives in [`apply_eligibility_filters()`](eu-call-finder/5_analysis/eligibility.py:1).
    """

    score = 10.0

    # Country/org-type eligibility may be missing from portal output; we treat
    # *missing* as mildly uncertain rather than fully eligible.
    eligible_countries = call_data.get("eligible_countries", [])
    eligible_types = call_data.get("eligible_organization_types", [])
    if not eligible_countries:
        score -= 0.5
    if not eligible_types:
        score -= 0.5

    # TRL requirement missing -> slight uncertainty
    if not call_data.get("trl"):
        score -= 0.5

    # Check budget feasibility if known
    budget = call_data.get("budget_per_project", {})
    max_budget = budget.get("max")

    if max_budget is None:
        score -= 0.5
    else:
        # SME preference for smaller budgets
        if company_profile.get("type") == "SME":
            if max_budget > 10000000:
                score -= 3.0
            elif max_budget > 5000000:
                score -= 1.5

    return max(1.0, round(score, 1))


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


def _assess_call_data_quality(call_data: dict) -> ScoreQuality:
    """Assess how complete the call data is for scoring.

    This is portal-agnostic and only inspects fields used by scorer/critic.
    """

    reasons: list[str] = []

    title = (call_data.get("title") or "").strip()
    content_desc = (call_data.get("content", {}) or {}).get("description") or ""
    content_desc = str(content_desc).strip()
    keywords = call_data.get("keywords") or []
    required_domains = call_data.get("required_domains") or []

    budget = call_data.get("budget_per_project") or {}
    budget_has_numbers = bool(budget.get("min") or budget.get("max"))

    deadline = ((call_data.get("general_info") or {}).get("dates") or {}).get(
        "deadline", ""
    )
    deadline = str(deadline).strip()

    # 6 “signals” used downstream; compute coverage.
    signals_total = 6
    signals_present = 0

    if title:
        signals_present += 1
    else:
        reasons.append("missing title")

    if len(content_desc) >= 80:
        signals_present += 1
    else:
        reasons.append("missing/short description")

    if isinstance(keywords, list) and len(keywords) >= 3:
        signals_present += 1
    else:
        reasons.append("missing/low keywords")

    if isinstance(required_domains, list) and len(required_domains) >= 1:
        signals_present += 1
    else:
        reasons.append("missing required_domains")

    if budget_has_numbers:
        signals_present += 1
    else:
        reasons.append("missing budget")

    if deadline:
        signals_present += 1
    else:
        reasons.append("missing deadline")

    coverage = signals_present / signals_total
    score = round(coverage * 100, 1)

    if coverage >= 0.84:
        level = "high"
    elif coverage >= 0.5:
        level = "medium"
    else:
        level = "low"

    return ScoreQuality(level=level, score=score, reasons=reasons)


def _apply_quality_penalty(total_raw: float, quality: ScoreQuality) -> float:
    """Apply a small downward adjustment when the call data is sparse.

    Goal: avoid misleading mid-scores (5-6) when the match is basically unknown.

    Penalty is capped and never pushes below 1.0.
    """

    # If data is good, do nothing.
    if quality.level == "high":
        return max(1.0, min(10.0, total_raw))

    # Mild penalty for medium quality; stronger for low.
    # Keep conservative: scoring remains primarily about fit, not completeness.
    penalty = 0.3 if quality.level == "medium" else 0.8

    adjusted = total_raw - penalty
    return max(1.0, min(10.0, adjusted))
