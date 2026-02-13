#!/usr/bin/env python3
"""
Simple test script for the Planner Agent.
Run this to verify the planner is working correctly.
"""

import sys
import os

# Add eu-call-finder to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from contracts.schemas import CompanyInput, CompanyProfile, Domain, DomainLevel
from planning import PlannerAgent, create_scraper_plan, STATIC_FILTER_CONFIG
import json


def test_basic_functionality():
    """Test basic planner functionality (no LLM required)."""
    print("=" * 70)
    print("TEST 1: Basic Functionality (Fallback Mode)")
    print("=" * 70)

    # Create a test company profile
    company_input = CompanyInput(
        company=CompanyProfile(
            name="AI Startup Bulgaria",
            description="We develop artificial intelligence solutions for healthcare diagnostics using computer vision and deep learning.",
            type="SME",
            employees=25,
            country="Bulgaria",
            city="Sofia",
            domains=[
                Domain(
                    name="Artificial Intelligence",
                    sub_domains=["Computer Vision", "Deep Learning"],
                    level=DomainLevel.ADVANCED,
                ),
                Domain(
                    name="Healthcare",
                    sub_domains=["Medical Diagnostics"],
                    level=DomainLevel.INTERMEDIATE,
                ),
            ],
        )
    )

    # Create planner without API key (triggers fallback mode)
    planner = PlannerAgent(openai_api_key="")
    plan = planner.create_plan(company_input)

    print("\n[OK] Plan created successfully!")
    print(f"\nCompany: {plan['company_name']}")
    print(f"Type: {plan['company_type']}")
    print(f"\n🔍 Search Queries ({len(plan['search_queries'])}):")
    for i, query in enumerate(plan["search_queries"], 1):
        print(f"  {i}. {query}")
    print(f"\n📊 Target Programs: {', '.join(plan['target_programs'])}")
    print(f"📈 Estimated Calls: {plan['estimated_calls']}")
    print(f"\n💡 Reasoning: {plan['reasoning']}")

    return True


def test_static_filter_config():
    """Verify the hardcoded filter configuration."""
    print("\n" + "=" * 70)
    print("TEST 2: Static Filter Configuration")
    print("=" * 70)

    print("\n📋 STATIC_FILTER_CONFIG (for EU Portal API):")
    print(json.dumps(STATIC_FILTER_CONFIG, indent=2))

    # Verify structure
    assert "bool" in STATIC_FILTER_CONFIG
    assert "must" in STATIC_FILTER_CONFIG["bool"]
    assert len(STATIC_FILTER_CONFIG["bool"]["must"]) == 3

    print("\n[OK] Filter config structure is correct!")
    print("   - Type filter: Grants (1) & Prizes (8)")
    print("   - Status filter: Open (31094501) & Forthcoming (31094502)")
    print("   - Period filter: 2021-2027")

    return True


def test_with_llm():
    """Test with LLM if API key is available."""
    print("\n" + "=" * 70)
    print("TEST 3: LLM Mode (if API key available)")
    print("=" * 70)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n[WARN]  No OPENAI_API_KEY found in environment.")
        print("   Skipping LLM test. Set OPENAI_API_KEY to enable.")
        return None

    company_input = CompanyInput(
        company=CompanyProfile(
            name="GreenTech Innovations",
            description="German company specializing in renewable energy solutions and smart grid technology for sustainable cities.",
            type="SME",
            employees=40,
            country="Germany",
            city="Berlin",
            domains=[
                Domain(
                    name="Renewable Energy",
                    sub_domains=["Solar", "Wind", "Smart Grid"],
                    level=DomainLevel.EXPERT,
                )
            ],
        )
    )

    print(f"\n🤖 Using model: {os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')}")
    planner = PlannerAgent()
    plan = planner.create_plan(company_input)

    print("\n[OK] LLM plan created successfully!")
    print(f"\n🔍 Search Queries ({len(plan['search_queries'])}):")
    for i, query in enumerate(plan["search_queries"], 1):
        print(f"  {i}. {query}")
    print(f"\n📊 Target Programs: {', '.join(plan['target_programs'])}")

    return True


def test_plan_structure():
    """Test that plan has all required fields."""
    print("\n" + "=" * 70)
    print("TEST 4: Plan Structure Validation")
    print("=" * 70)

    company_input = CompanyInput(
        company=CompanyProfile(
            name="Test Company",
            description="A test company for validation purposes.",
            type="SME",
            employees=10,
            country="France",
            domains=[
                Domain(name="Testing", sub_domains=[], level=DomainLevel.BEGINNER)
            ],
        )
    )

    planner = PlannerAgent(openai_api_key="")
    plan = planner.create_plan(company_input)

    required_fields = [
        "search_queries",
        "filter_config",
        "target_programs",
        "estimated_calls",
        "reasoning",
        "company_name",
        "company_type",
        "timestamp",
    ]

    print("\nChecking required fields:")
    for field in required_fields:
        assert field in plan, f"Missing field: {field}"
        print(f"  [OK] {field}")

    print("\n[OK] All required fields present!")

    return True


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("PLANNER AGENT TEST SUITE")
    print("=" * 70)

    results = []

    try:
        results.append(("Basic Functionality", test_basic_functionality()))
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        results.append(("Basic Functionality", False))

    try:
        results.append(("Static Filter Config", test_static_filter_config()))
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        results.append(("Static Filter Config", False))

    try:
        llm_result = test_with_llm()
        if llm_result is not None:
            results.append(("LLM Mode", llm_result))
    except Exception as e:
        print(f"\n[FAIL] LLM test failed: {e}")
        results.append(("LLM Mode", False))

    try:
        results.append(("Plan Structure", test_plan_structure()))
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        results.append(("Plan Structure", False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[OK] PASS" if result else "[FAIL] FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! Planner Agent is working correctly.")
    else:
        print(f"\n[WARN]  {total - passed} test(s) failed. Check output above.")
