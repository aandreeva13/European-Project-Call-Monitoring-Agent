"""
LLM-based qualitative analysis for EU project calls.
Uses OpenAI API for nuanced analysis of call-company fit.
API key loaded from environment variables (.env file).
"""

import os
import json
from typing import Dict, List, Optional
from dataclasses import dataclass


# LLM Configuration - API key from environment
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # openai, anthropic, etc.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))


@dataclass
class LLMResponse:
    """Structured response from LLM"""

    match_summary: str
    domain_matches: List[Dict]
    keyword_hits: List[str]
    relevant_past_projects: List[Dict]
    suggested_partners: List[str]
    estimated_effort_hours: str
    reasoning: str
    confidence: str  # high, medium, low


def perform_qualitative_analysis(call_data: dict, company_profile: dict) -> dict:
    """
    Perform LLM-based qualitative analysis of how well a call matches the company.
    Falls back to rule-based if LLM not configured.
    """

    # Check if LLM is configured
    if not is_llm_configured():
        # Fallback to rule-based analysis
        return perform_rule_based_analysis(call_data, company_profile)

    try:
        # Call LLM for analysis
        llm_result = call_llm_for_analysis(call_data, company_profile)

        # Convert to expected format
        return {
            "match_summary": llm_result.match_summary,
            "domain_matches": llm_result.domain_matches,
            "keyword_hits": llm_result.keyword_hits,
            "relevant_past_projects": llm_result.relevant_past_projects,
            "suggested_partners": llm_result.suggested_partners,
            "estimated_effort_hours": llm_result.estimated_effort_hours,
            "llm_reasoning": llm_result.reasoning,
            "llm_confidence": llm_result.confidence,
            "analysis_method": "llm",
        }

    except Exception as e:
        # Fallback to rule-based if LLM fails
        print(f"[LLM Error] {e}. Falling back to rule-based analysis.")
        result = perform_rule_based_analysis(call_data, company_profile)
        result["llm_error"] = str(e)
        return result


def is_llm_configured() -> bool:
    """Check if LLM API key is configured"""
    if LLM_PROVIDER == "openai":
        return bool(OPENAI_API_KEY)
    elif LLM_PROVIDER == "anthropic":
        return bool(ANTHROPIC_API_KEY)
    return False


def call_llm_for_analysis(call_data: dict, company_profile: dict) -> LLMResponse:
    """
    Call LLM API for qualitative analysis.
    Supports OpenAI and Anthropic.
    """

    # Build the prompt
    prompt = build_analysis_prompt(call_data, company_profile)

    if LLM_PROVIDER == "openai":
        return call_openai(prompt, call_data, company_profile)
    elif LLM_PROVIDER == "anthropic":
        return call_anthropic(prompt, call_data, company_profile)
    else:
        raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}")


def build_analysis_prompt(call_data: dict, company_profile: dict) -> str:
    """Build comprehensive prompt for LLM analysis"""

    # Extract key information
    call_title = call_data.get("title", "")
    call_desc = call_data.get("content", {}).get("description", "")[
        :2000
    ]  # Truncate if too long
    call_domains = call_data.get("required_domains", [])
    call_keywords = call_data.get("keywords", [])

    company_name = company_profile.get("name", "")
    company_domains = company_profile.get("domains", [])
    company_keywords = company_profile.get("keywords", {}).get("include", [])
    past_projects = company_profile.get("past_eu_projects", [])

    prompt = f"""You are an expert EU funding advisor analyzing how well a funding call matches a company's capabilities.

## COMPANY PROFILE
Name: {company_name}
Domains: {", ".join([d["name"] + f" ({d.get('level', 'unknown')})" for d in company_domains])}
Keywords: {", ".join(company_keywords)}
Past EU Projects: {", ".join([p["name"] + f" ({p['program']})" for p in past_projects])}

## FUNDING CALL
Title: {call_title}
Required Domains: {", ".join(call_domains)}
Keywords: {", ".join(call_keywords[:15])}

Description: {call_desc}

## YOUR TASK
Analyze how well this call matches the company. Provide:

1. MATCH SUMMARY: A 1-2 sentence summary (Excellent/Good/Moderate/Weak match)

2. DOMAIN MATCHES: List how company domains align with call requirements. For each match:
   - Company domain
   - Call requirement
   - Strength: strong/moderate/weak
   - Reasoning (1 sentence)

3. KEYWORD HITS: Which company keywords are present in the call

4. RELEVANT PAST PROJECTS: Which past EU projects are relevant to this call and why

5. SUGGESTED PARTNERS: 2-3 specific partner types or organizations that would strengthen the consortium

6. EFFORT ESTIMATE: Estimated hours needed for proposal (40-80, 80-150, 100-200, 200-300)

7. REASONING: 2-3 sentences explaining your analysis

8. CONFIDENCE: high/medium/low (how confident are you in this assessment)

Respond in valid JSON format:
{{
    "match_summary": "...",
    "domain_matches": [
        {{"your_domain": "...", "call_requirement": "...", "strength": "...", "reasoning": "..."}}
    ],
    "keyword_hits": ["...", "..."],
    "relevant_past_projects": [
        {{"project": "...", "program": "...", "relevance": "high/medium"}}
    ],
    "suggested_partners": ["..."],
    "estimated_effort_hours": "...",
    "reasoning": "...",
    "confidence": "..."
}}"""

    return prompt


def call_openai(prompt: str, call_data: dict, company_profile: dict) -> LLMResponse:
    """Call OpenAI API for analysis"""
    try:
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY)

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert EU funding advisor providing structured analysis in JSON format.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=LLM_TEMPERATURE,
            max_tokens=1500,
        )

        # Parse JSON response
        content = response.choices[0].message.content

        # Extract JSON from response (handle markdown code blocks)
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        data = json.loads(content.strip())

        return LLMResponse(
            match_summary=data.get("match_summary", ""),
            domain_matches=data.get("domain_matches", []),
            keyword_hits=data.get("keyword_hits", []),
            relevant_past_projects=data.get("relevant_past_projects", []),
            suggested_partners=data.get("suggested_partners", []),
            estimated_effort_hours=data.get("estimated_effort_hours", "80-150"),
            reasoning=data.get("reasoning", ""),
            confidence=data.get("confidence", "medium"),
        )

    except ImportError:
        raise ImportError("OpenAI library not installed. Run: pip install openai")
    except Exception as e:
        raise Exception(f"OpenAI API error: {e}")


def call_anthropic(prompt: str, call_data: dict, company_profile: dict) -> LLMResponse:
    """Call Anthropic API for analysis"""
    try:
        import anthropic

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1500,
            temperature=LLM_TEMPERATURE,
            system="You are an expert EU funding advisor providing structured analysis in JSON format.",
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse JSON response
        content = response.content[0].text

        # Extract JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        data = json.loads(content.strip())

        return LLMResponse(
            match_summary=data.get("match_summary", ""),
            domain_matches=data.get("domain_matches", []),
            keyword_hits=data.get("keyword_hits", []),
            relevant_past_projects=data.get("relevant_past_projects", []),
            suggested_partners=data.get("suggested_partners", []),
            estimated_effort_hours=data.get("estimated_effort_hours", "80-150"),
            reasoning=data.get("reasoning", ""),
            confidence=data.get("confidence", "medium"),
        )

    except ImportError:
        raise ImportError("Anthropic library not installed. Run: pip install anthropic")
    except Exception as e:
        raise Exception(f"Anthropic API error: {e}")


# =============================================================================
# RULE-BASED FALLBACK (Original Implementation)
# =============================================================================


def perform_rule_based_analysis(call_data: dict, company_profile: dict) -> dict:
    """Fallback rule-based analysis when LLM not available"""

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
        "analysis_method": "rule_based",
    }


def analyze_domain_matches(call_data: dict, company_profile: dict) -> list:
    """Analyze how company domains match call requirements."""
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
    """Analyze keyword matches between company and call."""
    include_keywords = set(
        k.lower() for k in company_profile.get("keywords", {}).get("include", [])
    )
    exclude_keywords = set(
        k.lower() for k in company_profile.get("keywords", {}).get("exclude", [])
    )
    call_keywords = set(k.lower() for k in call_data.get("keywords", []))
    call_text = (
        call_data.get("content", {}).get("description", "")
        + " "
        + call_data.get("title", "")
    )
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
    call_program = call_data.get("general_info", {}).get("programme", "")
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
    general_info = call_data.get("general_info", {})
    action_type = general_info.get("action_type", "")
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
