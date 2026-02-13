def perform_qualitative_analysis(call_data: dict, company_profile: dict) -> dict:
    """
    Perform LLM-based qualitative analysis of how well a call matches the company.
    Analyzes domain alignment, keyword relevance, and generates match summaries.
    """

    # Analyze domain matches with strength ratings
    domain_matches = analyze_domain_matches(call_data, company_profile)

    # Analyze keyword matches
    keyword_analysis = analyze_keyword_matches(call_data, company_profile)

    # Generate overall match summary
    match_summary = generate_match_summary(
        call_data, company_profile, domain_matches, keyword_analysis
    )

    # Find relevant past projects
    relevant_projects = find_relevant_past_projects(call_data, company_profile)

    return {
        "match_summary": match_summary,
        "domain_matches": domain_matches,
        "keyword_hits": keyword_analysis["hits"],
        "relevant_past_projects": relevant_projects,
        "suggested_partners": suggest_partners(call_data, company_profile),
        "estimated_effort_hours": estimate_effort(call_data, company_profile),
    }


def analyze_domain_matches(call_data: dict, company_profile: dict) -> list:
    """
    Analyze how company domains match call requirements.
    Returns list of matches with strength ratings (strong/moderate/weak).
    """
    company_domains = company_profile.get("domains", [])
    call_requirements = call_data.get("required_domains", [])

    if not company_domains or not call_requirements:
        return []

    matches = []

    for cd in company_domains:
        for req in call_requirements:
            match_strength = calculate_match_strength(cd, req)
            if match_strength != "none":
                matches.append(
                    {
                        "your_domain": cd["name"],
                        "call_requirement": req,
                        "strength": match_strength,
                        "your_level": cd.get("level", "unknown"),
                        "reasoning": generate_match_reasoning(cd, req, match_strength),
                    }
                )

    return matches


def calculate_match_strength(company_domain: dict, call_requirement: str) -> str:
    """Calculate the strength of a domain match."""
    cd_name = company_domain["name"].lower()
    cd_subdomains = [s.lower() for s in company_domain.get("sub_domains", [])]
    req_lower = call_requirement.lower()

    # Check direct domain name match
    if cd_name in req_lower or req_lower in cd_name:
        if company_domain.get("level") in ["expert", "advanced"]:
            return "strong"
        return "moderate"

    # Check subdomain matches
    subdomain_matches = sum(1 for sd in cd_subdomains if sd in req_lower)
    if subdomain_matches >= 2:
        return "strong"
    elif subdomain_matches == 1:
        return "moderate"

    # Check for related terms
    related_terms = get_related_terms(cd_name)
    if any(term in req_lower for term in related_terms):
        return "weak"

    return "none"


def get_related_terms(domain: str) -> list:
    """Get related terms for a domain."""
    term_map = {
        "artificial intelligence": [
            "ai",
            "machine learning",
            "ml",
            "deep learning",
            "neural network",
        ],
        "cybersecurity": [
            "security",
            "cyber",
            "threat",
            "protection",
            "nist",
            "iso 27001",
        ],
        "digital transformation": [
            "digitization",
            "digitalization",
            " Industry 4.0",
            "smart",
        ],
        "cloud": ["aws", "azure", "gcp", "saas", "paas", "iaas"],
        "data": ["big data", "analytics", "data science", "business intelligence"],
    }
    return term_map.get(domain.lower(), [])


def generate_match_reasoning(company_domain: dict, call_req: str, strength: str) -> str:
    """Generate reasoning text for a domain match."""
    level = company_domain.get("level", "")

    if strength == "strong":
        return f"Your {level} expertise in {company_domain['name']} directly aligns with the requirement for '{call_req}'."
    elif strength == "moderate":
        return (
            f"Your experience in {company_domain['name']} is relevant to '{call_req}'."
        )
    else:
        return f"Some overlap between {company_domain['name']} and '{call_req}'."


def analyze_keyword_matches(call_data: dict, company_profile: dict) -> dict:
    """
    Analyze keyword matches between company and call.
    """
    include_keywords = set(
        k.lower() for k in company_profile.get("keywords", {}).get("include", [])
    )
    exclude_keywords = set(
        k.lower() for k in company_profile.get("keywords", {}).get("exclude", [])
    )
    call_keywords = set(k.lower() for k in call_data.get("keywords", []))
    call_text = call_data.get("description", "") + " " + call_data.get("title", "")
    call_text_lower = call_text.lower()

    hits = []
    excluded_found = []

    # Check included keywords
    for kw in include_keywords:
        if kw in call_text_lower or kw in call_keywords:
            hits.append(kw)

    # Check excluded keywords
    for kw in exclude_keywords:
        if kw in call_text_lower:
            excluded_found.append(kw)

    return {
        "hits": hits,
        "excluded_found": excluded_found,
        "primary_matches": [h for h in hits if h in call_keywords],
        "secondary_matches": [h for h in hits if h not in call_keywords],
    }


def generate_match_summary(
    call_data: dict, company_profile: dict, domain_matches: list, keyword_analysis: dict
) -> str:
    """Generate a human-readable summary of the match."""
    strong_matches = [m for m in domain_matches if m["strength"] == "strong"]
    moderate_matches = [m for m in domain_matches if m["strength"] == "moderate"]
    keyword_count = len(keyword_analysis["hits"])

    if len(strong_matches) >= 2:
        domains_text = " and ".join([m["your_domain"] for m in strong_matches[:2]])
        return f"Excellent match. The call combines {domains_text} — your strongest domains. High relevance with {keyword_count} keyword matches."
    elif len(strong_matches) == 1:
        return f"Strong match in {strong_matches[0]['your_domain']}. Good alignment with your core competencies."
    elif len(moderate_matches) >= 2:
        return f"Good overall match with {len(moderate_matches)} relevant domains and {keyword_count} keyword matches."
    elif len(moderate_matches) == 1:
        return f"Moderate match in {moderate_matches[0]['your_domain']}. Worth considering."
    else:
        return f"Weak match. Limited alignment with your expertise."


def find_relevant_past_projects(call_data: dict, company_profile: dict) -> list:
    """Find past EU projects relevant to this call."""
    past_projects = company_profile.get("past_eu_projects", [])
    call_program = call_data.get("program", "")
    call_domains = call_data.get("required_domains", [])

    relevant = []

    for project in past_projects:
        score = 0

        # Same program bonus
        if call_program in project.get("program", ""):
            score += 3

        # Check domain relevance
        project_name = project.get("name", "").lower()
        for domain in call_domains:
            if any(term in project_name for term in domain.lower().split()):
                score += 2

        if score >= 2:
            relevant.append(
                {
                    "project": project["name"],
                    "program": project["program"],
                    "relevance": "high" if score >= 4 else "medium",
                }
            )

    return relevant


def suggest_partners(call_data: dict, company_profile: dict) -> list:
    """Suggest potential consortium partners based on call requirements."""
    consortium = call_data.get("consortium", {})
    min_partners = consortium.get("min_partners", 3)
    min_countries = consortium.get("min_countries", 3)

    suggestions = []

    # If SME needs more partners
    if min_partners > 1:
        suggestions.extend(
            [
                "Fraunhofer (Germany) — research partner",
                "University partners from EU countries",
                "Industry partners from different sectors",
            ]
        )

    return suggestions[:3]


def estimate_effort(call_data: dict, company_profile: dict) -> str:
    """Estimate proposal preparation effort in hours."""
    action_type = call_data.get("action_type", "")
    budget = call_data.get("budget_per_project", {}).get("max", 0)

    if "RIA" in action_type or "Innovation Action" in action_type:
        if budget > 3000000:
            return "200-300"
        else:
            return "100-200"
    elif budget > 1000000:
        return "80-150"
    else:
        return "40-80"
