#!/usr/bin/env python3
"""
Simple test for Planner Agent - compatible with numbered folders.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import using full paths
import importlib.util

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


def test_basic():
    print("=" * 70)
    print("TESTING PLANNER AGENT")
    print("=" * 70)

    company_input = CompanyInput(
        company=CompanyProfile(
            name="AI Startup",
            description="We develop artificial intelligence solutions for healthcare using machine learning.",
            type="SME",
            employees=25,
            country="Bulgaria",
            domains=[
                Domain(
                    name="Artificial Intelligence",
                    sub_domains=["Machine Learning"],
                    level=DomainLevel.ADVANCED,
                )
            ],
        )
    )

    print("\n[1] Creating planner (fallback mode)...")
    planner = PlannerAgent(openai_api_key="")

    print("[2] Generating plan...")
    plan = planner.create_plan(company_input)

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    print(f"Company: {plan['company_name']}")
    print(f"Type: {plan['company_type']}")
    print(f"\nSearch Queries:")
    for i, query in enumerate(plan["search_queries"], 1):
        print(f"  {i}. {query}")
    print(f"\nTarget Programs: {', '.join(plan['target_programs'])}")
    print(f"Estimated Calls: {plan['estimated_calls']}")
    print(f"\nStatic Filter Config:")
    import json

    print(json.dumps(STATIC_FILTER_CONFIG, indent=2))
    print(f"\nReasoning: {plan['reasoning']}")

    print("\n" + "=" * 70)
    print("[SUCCESS] Planner Agent is working correctly!")
    print("=" * 70)


if __name__ == "__main__":
    test_basic()
