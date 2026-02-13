#!/usr/bin/env python3
"""
Test workflow: Safety Check -> Planning (shows actual LLM results)
This demonstrates the implemented parts of the workflow.
"""

import sys
import os
import json

# Setup path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv

load_dotenv()

print("Loading modules...")

# Load contracts
import importlib.util

spec = importlib.util.spec_from_file_location("contracts", "contracts/schemas.py")
contracts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contracts)

CompanyInput = contracts.CompanyInput
CompanyProfile = contracts.CompanyProfile
Domain = contracts.Domain
DomainLevel = contracts.DomainLevel

# Load state
spec2 = importlib.util.spec_from_file_location("state", "contracts/state.py")
state_module = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(state_module)

create_initial_state = state_module.create_initial_state

# Load individual components (not the full master agent to avoid selenium dependency)
spec_safety = importlib.util.spec_from_file_location(
    "safety_guard", "1_safety/safety_guard.py"
)
safety_mod = importlib.util.module_from_spec(spec_safety)
spec_safety.loader.exec_module(safety_mod)
SafetyGuard = safety_mod.SafetyGuard

spec_validator = importlib.util.spec_from_file_location(
    "input_validator", "1_safety/input_validator.py"
)
validator_mod = importlib.util.module_from_spec(spec_validator)
spec_validator.loader.exec_module(validator_mod)
InputValidator = validator_mod.InputValidator

spec_planner = importlib.util.spec_from_file_location(
    "planner", "3_planning/planner.py"
)
planner_mod = importlib.util.module_from_spec(spec_planner)
spec_planner.loader.exec_module(planner_mod)
PlannerAgent = planner_mod.PlannerAgent
STATIC_FILTER_CONFIG = planner_mod.STATIC_FILTER_CONFIG


def test_safety_and_planning():
    """Run Safety Check and Planning with real LLM"""
    print("\n" + "=" * 70)
    print("EU CALL FINDER - SAFETY & PLANNING TEST")
    print("=" * 70)

    # Create company input
    print("\n[INPUT] COMPANY PROFILE:")
    print("-" * 70)

    company_input = CompanyInput(
        company=CompanyProfile(
            name="NexGen AI Solutions",
            description="Bulgarian AI company developing intelligent automation solutions for enterprise clients. Specialized in LLM applications, agentic AI and NLP. We build custom AI agents for business process automation, document analysis, and customer support.",
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
            ],
        )
    )

    print(f"Name: {company_input.company.name}")
    print(f"Type: {company_input.company.type}")
    print(f"Country: {company_input.company.country}")
    print(f"Employees: {company_input.company.employees}")
    print(f"\nDomains:")
    for d in company_input.company.domains:
        print(f"  * {d.name} ({d.level.value})")
        print(f"    Sub-domains: {', '.join(d.sub_domains)}")

    # Step 1: Safety Check
    print("\n" + "=" * 70)
    print("STEP 1: SAFETY CHECK & VALIDATION")
    print("=" * 70)

    print("\n[SECURITY] Running security checks...")
    guard = SafetyGuard(use_llm=False)  # Disable LLM for safety to avoid timeout
    safety_result = guard.check(company_input)

    if not safety_result.is_valid:
        print(f"\n[FAIL] SAFETY CHECK FAILED: {safety_result.reason}")
        return False

    print("[OK] Security check passed")
    print(f"   Score: {safety_result.score}/10")

    print("\n[VALIDATION] Running input validation...")
    validator = InputValidator()
    validation_result = validator.validate(company_input)

    if not validation_result.is_valid:
        print(f"\n[FAIL] VALIDATION FAILED: {validation_result.reason}")
        return False

    print("[OK] Input validation passed")
    print(f"   Score: {validation_result.score}/10")
    if validation_result.missing_fields:
        print(f"   Missing fields: {validation_result.missing_fields}")

    # Step 2: Planning
    print("\n" + "=" * 70)
    print("STEP 2: PLANNING (with LLM)")
    print("=" * 70)

    print(f"\n[AI] Using model: {os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')}")
    print("   Generating execution plan...")
    print("   (This may take 20-40 seconds)...")

    planner = PlannerAgent()
    plan = planner.create_plan(company_input)

    print("\n" + "=" * 70)
    print("[OK] PLAN GENERATED SUCCESSFULLY!")
    print("=" * 70)

    print(f"\n[SUMMARY] PLAN SUMMARY:")
    print(f"   Company: {plan['company_name']}")
    print(f"   Type: {plan['company_type']}")
    print(f"   Target Programs: {', '.join(plan['target_programs'])}")
    print(f"   Estimated Calls: {plan['estimated_calls']}")

    print(f"\n[SEARCH] SEARCH QUERIES ({len(plan['search_queries'])}):")
    for i, query in enumerate(plan["search_queries"], 1):
        print(f"   {i}. {query}")

    print(f"\n[INPUT] STATIC FILTER CONFIG (Hardcoded for EU Portal):")
    print(json.dumps(plan["filter_config"], indent=4))

    print(f"\n[REASON] REASONING:")
    print(f"   {plan['reasoning']}")

    print(f"\n[TIME]  Timestamp: {plan['timestamp']}")

    # Summary
    print("\n" + "=" * 70)
    print("WORKFLOW SUMMARY")
    print("=" * 70)
    print(f"[OK] Safety Check: PASSED")
    print(f"[OK] Input Validation: PASSED (score: {validation_result.score}/10)")
    print(f"[OK] Planning: COMPLETED ({len(plan['search_queries'])} search queries)")
    print(f"\n[STATS] Plan Quality:")
    print(f"   * {len(plan['search_queries'])} targeted search queries")
    print(f"   * {len(plan['target_programs'])} EU programs identified")
    print(f"   * ~{plan['estimated_calls']} estimated matching calls")
    print(f"   * Hardcoded filters for 2021-2027 period")

    print("\n" + "=" * 70)
    print("[OK] SAFETY & PLANNING TEST COMPLETED!")
    print("=" * 70)
    print("\n[VALIDATION] Next Step: Retrieval")
    print("   These search queries would be used to scrape the EU Funding Portal")
    print("   and find actual funding calls matching this company's profile.")

    return True


def test_with_different_companies():
    """Test with different company types to show versatility"""
    print("\n" + "=" * 70)
    print("ADDITIONAL TEST: Different Company Profile")
    print("=" * 70)

    # Green tech company
    company_input = CompanyInput(
        company=CompanyProfile(
            name="EcoEnergy Berlin",
            description="German renewable energy company specializing in solar panel optimization and smart grid integration. We develop IoT sensors for energy monitoring.",
            type="SME",
            employees=32,
            country="Germany",
            city="Berlin",
            domains=[
                Domain(
                    name="Renewable Energy",
                    sub_domains=["Solar Energy", "Smart Grid"],
                    level=DomainLevel.EXPERT,
                ),
                Domain(
                    name="IoT",
                    sub_domains=["Energy Monitoring", "Sensors"],
                    level=DomainLevel.ADVANCED,
                ),
            ],
        )
    )

    print(f"\nCompany: {company_input.company.name}")
    print(f"Country: {company_input.company.country}")
    print(f"Domain: {company_input.company.domains[0].name}")

    print("\n[AI] Generating plan...")
    planner = PlannerAgent()
    plan = planner.create_plan(company_input)

    print(f"\n[OK] Plan created!")
    print(f"   Target programs: {', '.join(plan['target_programs'])}")
    print(f"   Estimated calls: {plan['estimated_calls']}")
    print(f"\n   Top 3 queries:")
    for i, query in enumerate(plan["search_queries"][:3], 1):
        print(f"   {i}. {query}")


if __name__ == "__main__":
    print("\n" + ">>>>" * 17)
    print("EU CALL FINDER - WORKFLOW DEMONSTRATION")
    print(">>>>" * 17)

    print("\nThis test demonstrates:")
    print("  [OK] Safety & Security validation")
    print("  [OK] Input quality validation")
    print("  [OK] LLM-based planning with real EU programs")
    print("  [OK] Hardcoded EU Portal filters")
    print("  [OK] Targeted search query generation")

    try:
        success = test_safety_and_planning()

        if success:
            # Run additional test
            test_with_different_companies()

            print("\n" + "=" * 70)
            print("ALL TESTS PASSED!")
            print("=" * 70)
            print("\nThe Safety Guard and Planner are fully operational.")
            print("Ready for integration with Retrieval module.")
        else:
            print("\n[FAIL] Test failed")

    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback

        traceback.print_exc()
