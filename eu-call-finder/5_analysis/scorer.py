def score_call(call_data: dict, company_profile: dict) -> dict:
    """
    Score a call based on 6 criteria with weighted scoring (1-10 scale).
    Weights: Domain Match (30%), Keyword Match (15%), Eligibility (20%),
             Budget (15%), Strategic Value (10%), Deadline (10%)
    """

    # Domain Match (30%): Strong matches with expertise level bonus
    domain_score = _score_domain_match(call_data, company_profile)

    # Keyword Match (15%): With semantic equivalence and synonym matching
    keyword_score = _score_keyword_match(call_data, company_profile)

    # Eligibility Fit (20%): Weighted by importance of each check
    eligibility_score = _score_eligibility(call_data, company_profile)

    # Budget Feasibility (15%): Graduated scale based on distance from range
    budget_score = _score_budget_feasibility(call_data, company_profile)

    # Strategic Value (10%): Enhanced program matching with fallback
    strategic_score = _score_strategic_value(call_data, company_profile)

    # Deadline Comfort (10%): With urgency bonus for close deadlines
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

    return {
        "total": total,
        "domain_match": domain_score,
        "keyword_match": keyword_score,
        "eligibility_fit": eligibility_score,
        "budget_feasibility": budget_score,
        "strategic_value": strategic_score,
        "deadline_comfort": deadline_score,
        "recommendation": _get_recommendation(total),
    }


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

            # Direct domain match
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
        "generative ai": {"generative ai", "genai", "llm", "foundation models"},
        # Cybersecurity variations
        "cybersecurity": {
            "cybersecurity",
            "cyber security",
            "information security",
            "infosec",
            "it security",
            "network security",
        },
        "security": {"security", "cybersecurity", "information security", "protection"},
        "threat detection": {
            "threat detection",
            "threat intelligence",
            "intrusion detection",
            "security monitoring",
        },
        "cloud": {
            "cloud",
            "cloud computing",
            "aws",
            "azure",
            "gcp",
            "iaas",
            "paas",
            "saas",
        },
        "automation": {
            "automation",
            "automated",
            "robotic process automation",
            "rpa",
            "orchestration",
        },
        "digital transformation": {
            "digital transformation",
            "digitization",
            "digitalization",
            "industry 4.0",
        },
    }

    # Return equivalents if keyword is in map, else just the keyword
    return equivalents.get(keyword, {keyword})


def _score_keyword_match(call_data: dict, company_profile: dict) -> float:
    """Score based on keyword overlap with semantic matching."""
    company_keywords = company_profile.get("keywords", {}).get("include", [])
    call_keywords = call_data.get("keywords", [])
    call_text = (
        call_data.get("content", {}).get("description", "")
        + " "
        + call_data.get("title", "")
    ).lower()

    if not company_keywords:
        return 3.0

    # Expand company keywords to include semantic equivalents
    expanded_company_kw = set()
    for kw in company_keywords:
        expanded_company_kw.update(_expand_keyword(kw))

    # Check matches against call keywords and description
    matches = set()
    for kw in expanded_company_kw:
        # Check in explicit keywords
        for ck in call_keywords:
            if kw in ck.lower() or ck.lower() in kw:
                matches.add(kw)
                break

        # Check in call text (description/title)
        if kw in call_text:
            matches.add(kw)

    # Score based on match count
    match_count = len(matches)

    if match_count >= 6:
        return 9.5
    elif match_count >= 4:
        return 8.5
    elif match_count >= 3:
        return 7.0
    elif match_count == 2:
        return 5.5
    elif match_count == 1:
        return 4.0
    else:
        return 2.5


def _score_eligibility(call_data: dict, company_profile: dict) -> float:
    """Score based on eligibility checks with weighted importance."""
    eligibility = call_data.get("eligibility", {})

    # Weighted checks (country and type are critical, budget/TRL are adjustable)
    checks = [
        (eligibility.get("country_ok", False), 3.0),  # Critical
        (eligibility.get("type_ok", False), 2.5),  # Critical
        (eligibility.get("trl_ok", False), 1.5),  # Moderate
        (eligibility.get("budget_ok", False), 1.0),  # Can be worked around
    ]

    score = sum(weight for passed, weight in checks if passed)
    max_score = sum(weight for _, weight in checks)

    # Normalize to 1-10 scale
    normalized = 1.0 + (score / max_score) * 9.0

    # SME encouraged bonus
    if eligibility.get("sme_encouraged", False):
        normalized = min(10.0, normalized + 0.5)

    return round(normalized, 1)


def _score_budget_feasibility(call_data: dict, company_profile: dict) -> float:
    """Score based on budget range fit with graduated penalty, adjusted for program type."""
    search_params = company_profile.get("search_params", {})
    budget_range = search_params.get("budget_range", {})
    call_budget = call_data.get("budget_per_project", {})

    if not budget_range or not call_budget:
        return 6.0

    # Get budget values
    min_pref = budget_range.get("min", 0)
    max_pref = budget_range.get("max", float("inf"))
    min_call = call_budget.get("min", 0)
    max_call = call_budget.get("max", float("inf"))

    # Convert BGN to EUR roughly (1 EUR ≈ 1.95 BGN)
    call_currency = call_budget.get("currency", "EUR")
    if call_currency.upper() in ["BGN", "ЛВ", "ЛЕВА"]:
        min_call = min_call / 1.95 if min_call else 0
        max_call = max_call / 1.95 if max_call else float("inf")

    # Adjust expectations for Horizon Europe / large EU programs
    # These naturally have higher budgets, so be more lenient
    general_info = call_data.get("general_info", {})
    programme = general_info.get("programme", "").lower()
    is_horizon = "horizon" in programme or "eic" in programme

    # Multiplier for Horizon programs (less penalty for high budgets)
    horizon_multiplier = 1.5 if is_horizon else 1.0

    # Calculate overlap
    overlap_min = max(min_pref, min_call)
    overlap_max = min(max_pref, max_call)

    # Perfect overlap
    if overlap_max >= overlap_min:
        overlap_size = overlap_max - overlap_min
        preferred_range = max_pref - min_pref
        overlap_ratio = overlap_size / preferred_range if preferred_range > 0 else 1.0

        if overlap_ratio >= 0.8:
            return 9.0
        elif overlap_ratio >= 0.5:
            return 8.0
        else:
            return 7.0

    # Partial overlap - Call budget higher than preferred
    if min_call > max_pref:
        ratio = min_call / max_pref if max_pref > 0 else float("inf")
        adjusted_ratio = ratio / horizon_multiplier  # Horizon gets discount

        if adjusted_ratio <= 2.0:
            return 7.0  # Within 2x (or 3x for Horizon) - still good
        elif adjusted_ratio <= 4.0:
            return 5.5  # 3-4x - challenging but possible
        elif adjusted_ratio <= 8.0:
            return 4.0  # 4-8x - difficult, need consortium
        elif adjusted_ratio <= 15.0:
            return 2.5  # 8-15x - very difficult as SME partner
        else:
            return 1.5  # Way too high

    # Call budget lower than preferred
    elif max_call < min_pref:
        ratio = min_pref / max_call if max_call > 0 else float("inf")

        if ratio <= 2.0:
            return 7.0
        elif ratio <= 4.0:
            return 5.0
        else:
            return 3.5

    return 5.0


def _score_strategic_value(call_data: dict, company_profile: dict) -> float:
    """Score based on strategic alignment with past projects and sector fit."""
    past_projects = company_profile.get("past_eu_projects", [])
    call_program = call_data.get("general_info", {}).get("programme", "")

    # Check program experience
    if past_projects:
        program_matches = sum(
            1 for p in past_projects if call_program in p.get("program", "")
        )

        if program_matches >= 2:
            return 9.5
        elif program_matches == 1:
            return 8.0

    # Check sector/domain alignment without past project requirement
    company_domains = [d["name"].lower() for d in company_profile.get("domains", [])]
    call_title = call_data.get("title", "").lower()

    domain_in_title = sum(1 for d in company_domains if d in call_title)

    if domain_in_title >= 2:
        return 7.5
    elif domain_in_title == 1:
        return 6.5
    else:
        return 5.0  # Neutral baseline


def _score_deadline_comfort(call_data: dict) -> float:
    """Score based on days until deadline with urgency consideration."""
    from datetime import datetime
    import re

    # Extract deadline from general_info.dates.deadline
    general_info = call_data.get("general_info", {})
    dates = general_info.get("dates", {})
    deadline_str = dates.get("deadline", "")

    # Calculate days until deadline
    days = 0

    if deadline_str:
        # Parse date from various formats
        # Format: "18 September 2026 17:00:00 Brussels time" or "15 April 2026 17:00:00 Sofia time"

        # Extract date part (remove time and timezone)
        date_match = re.search(
            r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
            deadline_str,
            re.IGNORECASE,
        )

        if date_match:
            day = int(date_match.group(1))
            month_name = date_match.group(2).lower()
            year = int(date_match.group(3))

            # Convert month name to number
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
            month = months.get(month_name, 1)

            try:
                deadline_date = datetime(year, month, day)
                today = datetime.now()
                days = (deadline_date - today).days
            except:
                days = 0

    # Use pre-calculated days if available and parsing failed
    if days <= 0:
        days = call_data.get("days_until_deadline", 0)

    if days >= 270:  # 9+ months - plenty of time
        return 9.0
    elif days >= 180:  # 6-9 months - comfortable
        return 8.5
    elif days >= 90:  # 3-6 months - good
        return 7.5
    elif days >= 60:  # 2-3 months - manageable
        return 6.5
    elif days >= 30:  # 1-2 months - getting tight
        return 5.5
    elif days >= 14:  # 2-4 weeks - urgent but doable
        return 4.5
    elif days >= 7:  # 1-2 weeks - very urgent
        return 3.5
    else:
        return 2.0  # <1 week - probably too late


def _get_recommendation(score: float) -> dict:
    """Get recommendation based on total score with adjusted thresholds."""
    if score >= 8.0:
        return {"action": "apply", "label": "КАНДИДАТСТВАЙТЕ", "color": "green"}
    elif score >= 6.0:
        return {"action": "consider", "label": "ОБМИСЛЕТЕ", "color": "yellow"}
    elif score >= 4.0:
        return {"action": "monitor", "label": "НАБЛЮДАВАЙТЕ", "color": "blue"}
    else:
        return {"action": "skip", "label": "ПРОПУСНЕТЕ", "color": "red"}
