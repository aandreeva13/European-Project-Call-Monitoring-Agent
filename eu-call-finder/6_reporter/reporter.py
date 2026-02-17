"""
Reporter Module - Generates comprehensive LLM-powered reports with card-based structure.
Location: 6_reporter/reporter.py
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# LLM Configuration for Reporter
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL_REPORTER = os.getenv("LLM_MODEL_REPORTER", "gpt-4")


def is_llm_configured() -> bool:
    """Check if LLM API key is configured."""
    if LLM_PROVIDER == "openai":
        return bool(OPENAI_API_KEY)
    return False


def generate_comprehensive_report(analyzed_calls: list, company_input: dict) -> dict:
    """
    Main entry point: Generate comprehensive report with card-based structure.
    Uses LLM if available, otherwise falls back to rule-based generation.
    """
    if is_llm_configured():
        try:
            return generate_llm_report(analyzed_calls, company_input)
        except Exception as e:
            print(f"[REPORTER] LLM error: {e}. Using fallback.")
            return generate_fallback_report(analyzed_calls, company_input)
    else:
        return generate_fallback_report(analyzed_calls, company_input)


def generate_llm_report(analyzed_calls: list, company_input: dict) -> dict:
    """Generate comprehensive LLM-powered report with detailed cards."""

    print("[REPORTER] Generating LLM-powered report...")

    # Prepare company profile
    company = company_input.get("company", {})
    company_summary = {
        "name": company.get("name", "Unknown"),
        "type": company.get("type", "Unknown"),
        "description": company.get("description", ""),
        "country": company.get("country", ""),
        "employees": company.get("employees", 0),
        "domains": [
            {
                "name": d.get("name", ""),
                "level": d.get("level", ""),
                "sub_domains": d.get("sub_domains", []),
            }
            for d in company.get("domains", [])
        ],
    }

    # Prepare top calls for LLM analysis with ALL rich data
    top_calls = analyzed_calls[:5] if len(analyzed_calls) > 5 else analyzed_calls

    calls_for_llm = []
    for call in top_calls:
        # Extract all rich information from both raw_data and content
        raw_data = call.get("raw_data", {})
        content = call.get("content", {})
        general_info = call.get("general_info", {})

        # Get full description (prefer content.description, fallback to raw_data)
        full_description = content.get("description", "") or raw_data.get(
            "description", ""
        )
        destination = content.get("destination", "") or raw_data.get("destination", "")
        conditions = content.get("conditions", "") or raw_data.get("conditions", "")
        budget_info = call.get("budget", "N/A")

        # Get programme info
        prog_info = general_info.get("programme", "") or raw_data.get(
            "general_info", {}
        ).get("programme", "")
        action_type = general_info.get("action_type", "") or raw_data.get(
            "general_info", {}
        ).get("action_type", "")

        calls_for_llm.append(
            {
                "id": call.get("id", ""),
                "title": call.get("title", ""),
                "programme": call.get("programme", prog_info),
                "action_type": action_type,
                "budget": budget_info,
                "deadline": call.get("deadline", "N/A"),
                "relevance_score": call.get("relevance_score", 0),
                "eligibility_passed": call.get("eligibility_passed", False),
                "match_summary": call.get("match_summary", ""),
                "full_description": full_description[
                    :800
                ],  # Include substantial description
                "destination": destination[:400],  # Include destination context
                "eligibility_conditions": conditions[:400],  # Include eligibility info
                "url": call.get("url", ""),
            }
        )

    # Build LLM prompt
    prompt = build_llm_prompt(company_summary, calls_for_llm, len(analyzed_calls))

    # Call LLM
    if LLM_PROVIDER == "openai":
        from openai import OpenAI

        client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)

        response = client.chat.completions.create(
            model=LLM_MODEL_REPORTER,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert EU funding advisor. Generate detailed, actionable reports in JSON format. Always return complete, valid JSON.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )

        content = response.choices[0].message.content

        # Save raw LLM response to file for debugging
        debug_file = f"reporter_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(debug_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "company_name": company_summary.get("name"),
                    "llm_raw_response": content,
                    "analyzed_calls_count": len(analyzed_calls),
                },
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"[REPORTER] Debug info saved to: {debug_file}")

        # Parse JSON response - handle markdown code blocks and clean up
        cleaned_content = content.strip()  # Initialize here

        try:
            # Clean the content - remove markdown code blocks
            if cleaned_content.startswith("```"):
                # Remove opening code block
                cleaned_content = (
                    cleaned_content.split("\n", 1)[1]
                    if "\n" in cleaned_content
                    else cleaned_content
                )
                cleaned_content = cleaned_content.lstrip("`json").lstrip("`").strip()
            if cleaned_content.endswith("```"):
                # Remove closing code block
                cleaned_content = cleaned_content.rsplit("```", 1)[0].strip()

            # Remove any remaining markdown fences
            cleaned_content = (
                cleaned_content.replace("```json", "").replace("```", "").strip()
            )

            llm_report = json.loads(cleaned_content)
        except json.JSONDecodeError as e:
            print(f"[REPORTER] Failed to parse LLM response as JSON: {e}")
            print(f"[REPORTER] Attempting to extract JSON from response...")

            # Try to find JSON between curly braces
            try:
                # Find the first { and last }
                start = cleaned_content.find("{")
                end = cleaned_content.rfind("}")
                if start != -1 and end != -1 and end > start:
                    json_str = cleaned_content[start : end + 1]
                    llm_report = json.loads(json_str)
                    print("[REPORTER] Successfully extracted JSON from response")
                else:
                    raise ValueError("No JSON object found in response")
            except Exception as extract_error:
                print(f"[REPORTER] JSON extraction failed: {extract_error}")
                return generate_fallback_report(analyzed_calls, company_input)

        # Build final report with enriched cards
        final_report = {
            "report_type": "llm_enhanced",
            "generated_at": datetime.now().isoformat(),
            "company_profile": company_summary,
            "company_summary": llm_report.get("company_summary", {}),
            "top_recommendations": llm_report.get("top_recommendations", []),
            "overall_assessment": llm_report.get("overall_assessment", {}),
            "funding_cards": build_funding_cards(
                analyzed_calls, llm_report.get("top_recommendations", [])
            ),
            "total_calls": len(analyzed_calls),
        }

        return final_report
    else:
        # Handle unsupported LLM providers
        print(f"[REPORTER] Unsupported LLM provider: {LLM_PROVIDER}")
        return generate_fallback_report(analyzed_calls, company_input)


def build_llm_prompt(
    company_summary: dict, calls_for_llm: list, total_calls: int
) -> str:
    """Build detailed prompt for LLM report generation."""

    domains_str = "\n".join(
        [
            f"- {d['name']} (Level: {d['level']})"
            + (
                f", Specializations: {', '.join(d['sub_domains'])}"
                if d["sub_domains"]
                else ""
            )
            for d in company_summary["domains"]
        ]
    )

    def clean_text(text: str, max_length: int = 1000) -> str:
        """Clean text by escaping special characters and limiting length."""
        if not text:
            return ""
        # Replace newlines and tabs with spaces
        text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
        # Remove excessive whitespace
        text = " ".join(text.split())
        # Escape quotes to prevent prompt injection
        text = text.replace('"', '\\"')
        return text[:max_length]

    calls_str = "\n\n".join(
        [
            f"""CALL {i + 1}:
ID: {c["id"]}
Title: {clean_text(c["title"])}
Programme: {clean_text(c["programme"])}
Action Type: {clean_text(c.get("action_type", "N/A"))}
Budget: {clean_text(c["budget"])}
Deadline: {clean_text(c["deadline"])}
Relevance Score: {c["relevance_score"]}/10
Eligible: {"Yes" if c["eligibility_passed"] else "No"}
URL: {clean_text(c.get("url", "N/A"))}

FULL PROJECT DESCRIPTION:
{clean_text(c.get("full_description", "No detailed description available"), 800)}

DESTINATION & CONTEXT:
{clean_text(c.get("destination", "No destination information"), 400)}

ELIGIBILITY & CONDITIONS:
{clean_text(c.get("eligibility_conditions", "No eligibility details"), 400)}

Match Summary: {clean_text(c["match_summary"])}
"""
            for i, c in enumerate(calls_for_llm)
        ]
    )

    return f"""You are an expert EU funding advisor with deep knowledge of EU funding programs. Generate a comprehensive, professional report analyzing funding opportunities for this company.

COMPANY PROFILE:
Name: {company_summary["name"]}
Type: {company_summary["type"]}
Country: {company_summary["country"]}
Employees: {company_summary["employees"]}
Description: {company_summary["description"]}

Areas of Expertise:
{domains_str}

FUNDING OPPORTUNITIES FOUND ({total_calls} total):

{calls_str}

Generate a JSON report with this exact structure. Use professional, business-appropriate language:

{{
  "company_summary": {{
    "profile_overview": "A professional 2-3 sentence summary of the company, its expertise, and market position",
    "key_strengths": ["specific strength 1", "specific strength 2", "specific strength 3"],
    "recommended_focus_areas": ["area 1", "area 2"]
  }},
  "top_recommendations": [
    {{
      "call_id": "USE THE EXACT ID FROM ABOVE",
      "priority_rank": 1,
      "match_percentage": 95,
      "project_overview": "A detailed, professional explanation of what this funding project is about, its goals, target beneficiaries, and expected outcomes. Write 3-4 sentences using the FULL PROJECT DESCRIPTION provided above.",
      "why_recommended": "A thorough analysis explaining why this company is a good match. Reference specific elements from the company's profile and the project's requirements. Be specific about synergies.",
      "key_benefits": ["Specific benefit 1 with context", "Specific benefit 2 with context", "Specific benefit 3 with context"],
      "action_items": ["Specific actionable step 1", "Specific actionable step 2", "Specific actionable step 3"],
      "success_probability": "high/medium/low",
      "project_url": "USE THE URL FROM ABOVE"
    }}
  ],
  "overall_assessment": {{
    "total_opportunities": {total_calls},
    "high_priority_count": 0,
    "medium_priority_count": 0,
    "low_priority_count": 0,
    "summary_text": "A comprehensive assessment of the funding landscape for this company, mentioning the quality of matches and overall opportunities",
    "strategic_advice": "Detailed, actionable strategic recommendations for approaching EU funding, including next steps and timeline considerations"
  }}
}}

IMPORTANT INSTRUCTIONS:
1. Use the FULL PROJECT DESCRIPTION provided to write detailed project_overviews
2. Reference specific eligibility conditions and requirements
3. Make connections between the company's expertise and project goals
4. Write in professional business language, not casual
5. Include specific details from the data provided, don't be generic
6. The call_id must match the exact ID field from the calls above

Return ONLY valid JSON, no markdown formatting."""


def build_funding_cards(analyzed_calls: list, recommendations: list) -> list:
    """Build enriched funding cards with match percentages and details."""
    cards = []

    # Create mapping of recommendations by call_id OR title (LLM might use either)
    rec_map = {}
    for r in recommendations:
        # Try to match by ID first, then by title
        call_id = r.get("call_id", "")
        rec_map[call_id] = r
        # Also map by title if different
        if call_id and call_id not in [c.get("id", "") for c in analyzed_calls]:
            # LLM used title as ID, try to find matching call by title
            for call in analyzed_calls:
                if (
                    call.get("title", "").lower() in call_id.lower()
                    or call_id.lower() in call.get("title", "").lower()
                ):
                    rec_map[call.get("id", "")] = r
                    break

    for call in analyzed_calls:
        call_id = call.get("id", "")
        call_title = call.get("title", "")
        relevance_score = call.get("relevance_score", 0)

        # Try to find recommendation by ID, then by title match
        rec = rec_map.get(call_id, {})
        if not rec:
            # Try matching by title
            for r in recommendations:
                if (
                    call_title.lower() in r.get("call_id", "").lower()
                    or r.get("call_id", "").lower() in call_title.lower()
                ):
                    rec = r
                    break

        # Calculate match percentage (0-100)
        match_percentage = rec.get("match_percentage", int(relevance_score * 10))

        card = {
            "id": call_id,
            "title": call.get("title", "Untitled"),
            "programme": call.get("programme", ""),
            "description": call.get("raw_data", {}).get("description", ""),
            "short_summary": rec.get("project_overview", call.get("match_summary", "")),
            "match_percentage": match_percentage,
            "relevance_score": relevance_score,
            "eligibility_passed": call.get("eligibility_passed", False),
            "budget": call.get("budget", "N/A"),
            "deadline": call.get("deadline", "N/A"),
            "url": rec.get("project_url", call.get("url", "")),
            "status": call.get("status", ""),
            "tags": call.get("keyword_hits", []),
            "why_recommended": rec.get(
                "why_recommended", call.get("match_summary", "")
            ),
            "key_benefits": rec.get("key_benefits", []),
            "action_items": rec.get("action_items", []),
            "success_probability": rec.get("success_probability", "medium"),
            "domain_matches": call.get("domain_matches", []),
            "suggested_partners": call.get("suggested_partners", []),
        }
        cards.append(card)

    # Sort by match percentage
    cards.sort(key=lambda x: x["match_percentage"], reverse=True)
    return cards


def generate_fallback_report(analyzed_calls: list, company_input: dict) -> dict:
    """Generate a fallback report without LLM using rule-based logic."""

    print("[REPORTER] Generating fallback report...")

    company = company_input.get("company", {})

    # Build basic cards
    cards = []
    for call in analyzed_calls:
        relevance = call.get("relevance_score", 0)
        match_pct = int(relevance * 10)

        # Determine priority based on score
        if match_pct >= 80:
            priority = "high"
        elif match_pct >= 60:
            priority = "medium"
        else:
            priority = "low"

        card = {
            "id": call.get("id", ""),
            "title": call.get("title", "Untitled"),
            "programme": call.get("programme", ""),
            "description": call.get("raw_data", {}).get("description", "")[:300] + "..."
            if len(call.get("raw_data", {}).get("description", "")) > 300
            else call.get("raw_data", {}).get("description", ""),
            "short_summary": call.get("match_summary", ""),
            "match_percentage": match_pct,
            "relevance_score": relevance,
            "eligibility_passed": call.get("eligibility_passed", False),
            "budget": call.get("budget", "N/A"),
            "deadline": call.get("deadline", "N/A"),
            "url": call.get("url", ""),
            "status": call.get("status", ""),
            "tags": call.get("keyword_hits", []),
            "why_recommended": f"Match score: {relevance}/10 - "
            + call.get("match_summary", "")[:100],
            "key_benefits": [
                f"Relevance score: {relevance}/10",
                "EU funding opportunity"
                if call.get("eligibility_passed")
                else "Check eligibility requirements",
            ],
            "action_items": [
                "Review full call details",
                "Check eligibility requirements",
                "Note deadline: " + call.get("deadline", "TBD"),
            ],
            "success_probability": "high"
            if match_pct >= 80
            else "medium"
            if match_pct >= 60
            else "low",
            "domain_matches": call.get("domain_matches", []),
            "suggested_partners": call.get("suggested_partners", []),
        }
        cards.append(card)

    cards.sort(key=lambda x: x["match_percentage"], reverse=True)

    # Count priorities
    high_priority = len([c for c in cards if c["match_percentage"] >= 80])
    medium_priority = len([c for c in cards if 60 <= c["match_percentage"] < 80])
    low_priority = len([c for c in cards if c["match_percentage"] < 60])

    # Get domain names for strengths
    domains = company.get("domains", [])
    key_strengths = [d.get("name", "") for d in domains if d.get("name")]

    return {
        "report_type": "fallback",
        "generated_at": datetime.now().isoformat(),
        "company_profile": {
            "name": company.get("name", "Unknown"),
            "type": company.get("type", ""),
            "country": company.get("country", ""),
            "employees": company.get("employees", 0),
            "description": company.get("description", ""),
            "domains": domains,
        },
        "company_summary": {
            "profile_overview": f"{company.get('name', 'Company')} is a {company.get('type', 'organization')} based in {company.get('country', 'EU')} with {company.get('employees', 0)} employees and expertise in {', '.join([d.get('name', '') for d in domains[:3]])}.",
            "key_strengths": key_strengths
            if key_strengths
            else ["EU-based organization", "Seeking funding opportunities"],
            "recommended_focus_areas": [d.get("name", "") for d in domains[:2]],
        },
        "top_recommendations": [
            {
                "call_id": c["id"],
                "priority_rank": i + 1,
                "match_percentage": c["match_percentage"],
                "why_recommended": c["why_recommended"],
                "success_probability": c["success_probability"],
            }
            for i, c in enumerate(cards[:3])
        ],
        "overall_assessment": {
            "total_opportunities": len(analyzed_calls),
            "high_priority_count": high_priority,
            "medium_priority_count": medium_priority,
            "low_priority_count": low_priority,
            "summary_text": f"Found {len(analyzed_calls)} funding opportunities matching the company profile. {high_priority} high-priority opportunities identified.",
            "strategic_advice": "Focus on high-priority opportunities (80%+ match) first. Prepare applications well before deadlines. Consider forming consortiums for larger projects.",
        },
        "funding_cards": cards,
        "total_calls": len(analyzed_calls),
    }
