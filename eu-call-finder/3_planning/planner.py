"""
Planner Agent for EU Call Finder.
Translates company profiles into execution plans for the Web Scraper.
Uses LLM to generate targeted search queries and combines with hardcoded API filters.
"""

import os
import json
from typing import List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from contracts.schemas import CompanyInput

# HARDCODED filter configuration for EU Funding Portal API compatibility
STATIC_FILTER_CONFIG = {
    "bool": {
        "must": [
            {"terms": {"type": ["1", "8"]}},  # Grants & Prizes
            {"terms": {"status": ["31094501", "31094502"]}},  # Open & Forthcoming
            {"term": {"programmePeriod": "2021 - 2027"}},
        ]
    }
}


@dataclass
class ScraperPlan:
    """Execution plan for the web scraper."""

    search_queries: List[str]
    filter_config: Dict[str, Any]
    target_programs: List[str]
    estimated_calls: int
    reasoning: str


class PlannerAgent:
    """
    Planner Agent that creates execution plans from company profiles.
    Uses LLM to:
    1. Analyze company description and domains
    2. Generate targeted STRICT BOOLEAN search queries
    3. Identify relevant EU programs
    """

    # Supported EU Funding Programs
    EU_PROGRAMS = [
        "Horizon Europe",
        "Digital Europe",
        "LIFE Programme",
        "Erasmus+",
        "Creative Europe",
        "EU4Health",
        "European Defence Fund",
    ]

    def __init__(self, openai_api_key: str = None, model: str = None):
        """
        Initialize the Planner Agent.
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5.2")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    def create_plan(self, company_input: CompanyInput) -> Dict[str, Any]:
        """
        Create an execution plan from company input.
        """
        # Step 1: Use LLM to analyze and generate queries
        llm_result = self._generate_plan_with_llm(company_input)

        # Step 2: Combine with hardcoded filters
        plan = {
            "search_queries": llm_result["search_queries"],
            "filter_config": STATIC_FILTER_CONFIG,
            "target_programs": llm_result["target_programs"],
            "estimated_calls": llm_result["estimated_calls"],
            "reasoning": llm_result["reasoning"],
            "company_name": company_input.company.name,
            "company_type": company_input.company.type,
            "timestamp": self._get_timestamp(),
        }
        return plan

    def _generate_plan_with_llm(self, company_input: CompanyInput) -> Dict[str, Any]:
        """
        Use LLM to analyze company profile and generate search plan.
        """
        if not self.openai_api_key:
            # Fallback: Generate basic queries without LLM
            return self._generate_fallback_plan(company_input)

        try:
            import openai

            client = openai.OpenAI(
                api_key=self.openai_api_key, base_url=self.openai_base_url
            )
            prompt = self._create_planning_prompt(company_input)

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert EU funding advisor. You generate STRICT Boolean search queries for the Funding & Tenders Portal.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,  # Low temp for stricter formatting
                max_tokens=1000,
            )
            content = response.choices[0].message.content
            return self._parse_llm_response(content, company_input)
        except Exception as e:
            print(f"LLM planning failed: {str(e)}. Using fallback.")
            return self._generate_fallback_plan(company_input)

    def _create_planning_prompt(self, company_input: CompanyInput) -> str:
        """Create a prompt for the LLM to generate strict boolean queries."""
        company = company_input.company

        # Format domains
        domains_str = ", ".join([d.name for d in company.domains])

        prompt = f"""Analyze this company profile and create a search plan.
COMPANY: {company.name} ({company.type})
DESC: {company.description}
DOMAINS: {domains_str}

YOUR TASK:
Generate 5 STRICT BOOLEAN search queries compatible with the EU Portal.

### STRICT FORMATTING RULES (DO NOT VIOLATE):
1. **NO Natural Language:** Do not return "Find me robots".
2. **NO Single Quotes:** Do not use 'Robot'.
3. **Escaped Double Quotes:** Multi-word phrases MUST be wrapped in escaped double quotes. Example: "Artificial Intelligence"
4. **Uppercase Operators:** Use only AND, OR.
5. **Structure:** Concept A AND Concept B
6. **Relevance:** Combine a technical term with an application area.

Respond with JSON:
{{
    "search_queries": [
        "\"Artificial Intelligence\" AND Healthcare",
        "Robotics AND \"Medical Devices\""
    ],
    "target_programs": ["Horizon Europe", "Digital Europe"],
    "estimated_calls": 10,
    "reasoning": "Explanation..."
}}"""
        return prompt

    def _parse_llm_response(
        self, content: str, company_input: CompanyInput
    ) -> Dict[str, Any]:
        """Parse LLM response into structured plan data."""
        try:
            # Extract JSON from response
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].strip()
            else:
                json_str = content.strip()

            result = json.loads(json_str)
            search_queries = result.get("search_queries", [])

            if not search_queries:
                raise ValueError("No queries returned")

            return result
        except Exception as e:
            print(f"Failed to parse LLM response: {str(e)}")
            return self._generate_fallback_plan(company_input)

    def _generate_fallback_plan(self, company_input: CompanyInput) -> Dict[str, Any]:
        """Generate a basic plan without LLM when API is unavailable."""
        company = company_input.company
        queries = []

        # Fallback Strategy: Create strict boolean queries from domains
        for domain in company.domains:
            term = domain.name
            # If multi-word, wrap in quotes
            if " " in term:
                term = f'"{term}"'
            queries.append(term)

        # Combine first two domains if available
        if len(company.domains) >= 2:
            t1 = company.domains[0].name
            t2 = company.domains[1].name
            if " " in t1:
                t1 = f'"{t1}"'
            if " " in t2:
                t2 = f'"{t2}"'
            queries.append(f"{t1} AND {t2}")

        return {
            "search_queries": queries,
            "target_programs": ["Horizon Europe"],
            "estimated_calls": 0,
            "reasoning": "Fallback plan: Generated from domain names due to LLM failure.",
        }

    def _get_timestamp(self) -> str:
        """Get current timestamp for the plan."""
        from datetime import datetime

        return datetime.now().isoformat()


# Convenience function
def create_scraper_plan(
    company_input: CompanyInput, openai_api_key: str = None
) -> Dict[str, Any]:
    planner = PlannerAgent(openai_api_key=openai_api_key)
    return planner.create_plan(company_input)
