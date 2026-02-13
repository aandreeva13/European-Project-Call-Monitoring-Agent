#!/usr/bin/env python3
"""
Test Planner Agent with LLM (using your env configuration).
"""

import sys
import os

# Load env variables
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import using importlib to handle numbered folders
import importlib.util

# Load contracts
spec = importlib.util.spec_from_file_location("contracts", "contracts/schemas.py")
contracts_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contracts_module)

CompanyInput = contracts_module.CompanyInput
CompanyProfile = contracts_module.CompanyProfile
Domain = contracts_module.Domain
DomainLevel = contracts_module.DomainLevel

# Load planner
spec2 = importlib.util.spec_from_file_location("planner", "3_planning/planner.py")
planner_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(planner_module)

PlannerAgent = planner_module.PlannerAgent
STATIC_FILTER_CONFIG = planner_module.STATIC_FILTER_CONFIG


def test_with_llm():
    print("=" * 70)
    print("TESTING PLANNER AGENT WITH LLM")
    print("=" * 70)
    print(f"\nAPI Key: {os.getenv('OPENAI_API_KEY')[:15]}...")
    print(f"Model: {os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')}")
    print(f"Base URL: {os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')}")

    company_input = CompanyInput(
        company=CompanyProfile(
            name="NexGen AI Solutions",
            description="Bulgarian AI company developing intelligent automation solutions for enterprise clients. Specialized in LLM applications, agentic AI and NLP. We build custom AI agents for business process automation, document analysis, and customer support. Our team of 45 engineers has expertise in machine learning, computer vision, and conversational AI.",
            type="SME",
            employees=45,
            country="Bulgaria",
            city="Sofia",
            domains=[
                Domain(
                    name="Artificial Intelligence",
                    sub_domains=["Machine Learning", "NLP", "Agentic AI", "LLM"],
                    level=DomainLevel.ADVANCED,
                ),
                Domain(
                    name="Process Automation",
                    sub_domains=["Business Process Automation", "Document Analysis"],
                    level=DomainLevel.ADVANCED,
                ),
                Domain(
                    name="Enterprise Software",
                    sub_domains=["Conversational AI", "Customer Support"],
                    level=DomainLevel.INTERMEDIATE,
                ),
            ],
        )
    )

    print("\n[1] Creating planner with LLM...")
    planner = PlannerAgent()

    print("[2] Generating plan (this may take 10-20 seconds)...")
    try:
        plan = planner.create_plan(company_input)

        print("\n" + "=" * 70)
        print("LLM GENERATED PLAN")
        print("=" * 70)
        print(f"\nCompany: {plan['company_name']}")
        print(f"Type: {plan['company_type']}")
        print(f"Timestamp: {plan['timestamp']}")

        print(f"\n[SEARCH QUERIES] ({len(plan['search_queries'])}):")
        for i, query in enumerate(plan["search_queries"], 1):
            print(f"  {i}. {query}")

        print(f"\n[TARGET PROGRAMS]:")
        for prog in plan["target_programs"]:
            print(f"  - {prog}")

        print(f"\n[ESTIMATED CALLS]: {plan['estimated_calls']}")

        print(f"\n[STATIC FILTERS] (Hardcoded for EU Portal):")
        import json

        print(json.dumps(plan["filter_config"], indent=2))

        print(f"\n[REASONING]:")
        print(f"  {plan['reasoning']}")

        print("\n" + "=" * 70)
        print("[SUCCESS] LLM planning completed!")
        print("=" * 70)

    except Exception as e:
        print(f"\n[ERROR] LLM call failed: {e}")
        print("Falling back to basic mode...")

        planner = PlannerAgent(openai_api_key="")
        plan = planner.create_plan(company_input)

        print("\n[FALLBACK MODE RESULTS]")
        print(f"Company: {plan['company_name']}")
        print(f"Search Queries: {plan['search_queries']}")
        print(f"Reason: {plan['reasoning']}")


if __name__ == "__main__":
    test_with_llm()
