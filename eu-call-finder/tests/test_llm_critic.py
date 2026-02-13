#!/usr/bin/env python3
"""
Test LLM critic with real OpenAI API.
Run this after setting OPENAI_API_KEY in .env file.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from analysis.llm_critic import (
    perform_qualitative_analysis,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    ENABLE_LLM_ANALYSIS
)


def test_llm_with_sample_call():
    """Test LLM critic with a sample EU funding call."""
    
    # Check if API key is configured
    if not OPENAI_API_KEY or OPENAI_API_KEY == "your_openai_api_key_here"::
        print("❌ ERROR: OPENAI_API_KEY not configured!")
        print("   Please set your API key in the .env file:")
        print("   OPENAI_API_KEY=sk-your-actual-key-here")
        return
    
    if not ENABLE_LLM_ANALYSIS:
        print("⚠️  WARNING: ENABLE_LLM_ANALYSIS is set to false")
        print("   Set it to true in .env to use LLM")
        return
    
    print("=" * 80)
    print("LLM CRITIC TEST")
    print("=" * 80)
    print(f"\nUsing model: {OPENAI_MODEL}")
    print(f"API Key: {'✓ Configured' if OPENAI_API_KEY else '✗ Missing'}")
    print()
    
    # Sample call data (AI + Cybersecurity - should be a good match)
    call_data = {
        "id": "HORIZON-CL4-2026-HUMAN-01-03",
        "title": "Trustworthy AI for cybersecurity of critical infrastructure",
        "general_info": {
            "programme": "Horizon Europe (HORIZON)",
            "action_type": "HORIZON-RIA",
            "dates": {
                "deadline": "18 September 2026 17:00:00 Brussels time"
            }
        },
        "content": {
            "description": "Development of trustworthy AI systems for cybersecurity of critical infrastructure. Projects should address AI-based threat detection, anomaly detection, and automated response systems. Required expertise in machine learning, cybersecurity frameworks, and NIS2 compliance. SMEs are particularly encouraged to participate."
        },
        "required_domains": ["Artificial Intelligence", "Cybersecurity", "Critical Infrastructure Protection"],
        "keywords": ["artificial intelligence", "AI", "cybersecurity", "trustworthy AI", "NIS2", "threat detection", "machine learning"],
        "budget_per_project": {"min": 3000000, "max": 5000000, "currency": "EUR"},
        "consortium": {"min_partners": 3, "min_countries": 3},
        "trl": "4-7"
    }
    
    # Company profile
    company_profile = {
        "name": "NexGen AI Solutions",
        "type": "SME",
        "country": "Bulgaria",
        "domains": [
            {"name": "Artificial Intelligence", "sub_domains": ["Machine Learning", "NLP", "Computer Vision"], "level": "advanced"},
            {"name": "Cybersecurity", "sub_domains": ["Threat Detection", "SOC Operations", "NIS2 Compliance"], "level": "expert"}
        ],
        "keywords": {"include": ["artificial intelligence", "cybersecurity", "machine learning", "NLP", "AI"]},
        "past_eu_projects": [
            {"name": "AI4Manufacturing", "program": "Horizon 2020", "role": "partner", "year": 2023},
            {"name": "CyberSME", "program": "DIGITAL Europe", "role": "work_package_leader", "year": 2024}
        ]
    }
    
    print("Testing with sample call:")
    print(f"  ID: {call_data['id']}")
    print(f"  Title: {call_data['title']}")
    print(f"  Expected: Strong match (AI + Cybersecurity)")
    print()
    
    try:
        print("Calling LLM (this may take 5-10 seconds)...")
        print()
        
        # Run LLM analysis
        result = perform_qualitative_analysis(call_data, company_profile)
        
        # Display results
        print("=" * 80)
        print("RESULTS")
        print("=" * 80)
        print()
        
        print(f"Analysis Method: {result.get('analysis_method', 'unknown')}")
        print()
        
        print(f"Match Summary:")
        print(f"  {result['match_summary']}")
        print()
        
        print(f"Domain Matches ({len(result['domain_matches'])}):")
        for match in result['domain_matches']:
            print(f"  • {match['your_domain']} → {match['call_requirement']}")
            print(f"    Strength: {match['strength']} | {match['reasoning']}")
        print()
        
        print(f"Keyword Hits ({len(result['keyword_hits'])}):")
        print(f"  {', '.join(result['keyword_hits'])}")
        print()
        
        print(f"Suggested Partners ({len(result['suggested_partners'])}):")
        for partner in result['suggested_partners']:
            print(f"  • {partner}")
        print()
        
        print(f"Estimated Effort: {result['estimated_effort_hours']} hours")
        print()
        
        if 'llm_reasoning' in result:
            print(f"LLM Reasoning:")
            print(f"  {result['llm_reasoning']}")
            print()
        
        if 'llm_confidence' in result:
            print(f"LLM Confidence: {result['llm_confidence']}")
            print()
        
        if 'llm_error' in result:
            print(f"⚠️  LLM Error: {result['llm_error']}")
            print()
        
        print("=" * 80)
        print("✓ Test completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        print()
        print("=" * 80)
        print("❌ ERROR")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check your OPENAI_API_KEY in .env")
        print("2. Ensure you have internet connection")
        print("3. Check if you have credits in your OpenAI account")
        print("4. Try setting SKIP_LLM_ON_ERROR=true to test fallback")


def test_llm_disabled():
    """Test that critic falls back to rule-based when LLM disabled."""
    print("\n" + "=" * 80)
    print("TEST 2: LLM Disabled Fallback")
    print("=" * 80)
    print()
    
    # Temporarily disable LLM
    import analysis.llm_critic as llm_module
    original_setting = llm_module.ENABLE_LLM_ANALYSIS
    llm_module.ENABLE_LLM_ANALYSIS = False
    
    call_data = {
        "id": "TEST-001",
        "title": "Test Call",
        "content": {"description": "Test description"},
        "required_domains": ["Artificial Intelligence"],
        "keywords": ["AI", "machine learning"],
        "general_info": {"programme": "Test Program"}
    }
    
    company_profile = {
        "name": "Test Company",
        "domains": [{"name": "Artificial Intelligence", "level": "advanced"}],
        "keywords": {"include": ["AI"]},
        "past_eu_projects": []
    }
    
    try:
        result = perform_qualitative_analysis(call_data, company_profile)
        
        if result.get('analysis_method') == 'rule_based':
            print("✓ Successfully fell back to rule-based analysis")
            print(f"  Method: {result['analysis_method']}")
            print(f"  Match summary: {result['match_summary'][:80]}...")
        else:
            print("✗ Did not use fallback method")
            
    finally:
        # Restore original setting
        llm_module.ENABLE_LLM_ANALYSIS = original_setting


if __name__ == "__main__":
    # Test 1: LLM analysis (if configured)
    test_llm_with_sample_call()
    
    # Test 2: Fallback when disabled
    test_llm_disabled()
