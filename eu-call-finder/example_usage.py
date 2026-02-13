"""
Example usage of the Input Validator.

This script demonstrates how to use the validation system with the simplified input.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from contracts.schemas import CompanyInput, CompanyProfile, Domain, DomainLevel
from safety.input_validator import InputValidator


def example_basic_validation():
    """Example with basic validation only (no LLM)."""

    # Create a company profile
    company_input = CompanyInput(
        company=CompanyProfile(
            name="TechStart BG",
            description="We are a startup company that builds software solutions for businesses.",
            type="SME",
            employees=15,
            country="Bulgaria",
            city="Sofia",
            domains=[
                Domain(
                    name="Software Development",
                    sub_domains=["Web Applications", "Mobile Apps"],
                    level=DomainLevel.ADVANCED,
                )
            ],
        )
    )

    # Validate without LLM (no API key provided)
    validator = InputValidator()
    result = validator.validate(company_input)

    print("=== Basic Validation Example ===")
    print(f"Is Valid: {result.is_valid}")
    print(f"Score: {result.score}/10")
    print(f"Missing Fields: {result.missing_fields}")
    print(f"Reason: {result.reason}")
    print()


def example_with_llm():
    """Example with LLM validation (requires OPENAI_API_KEY)."""

    # Create a detailed company profile
    company_input = CompanyInput(
        company=CompanyProfile(
            name="NexGen AI Solutions",
            description=(
                "Bulgarian AI company developing intelligent automation solutions for enterprise clients. "
                "Specialized in LLM applications, agentic AI and natural language processing. "
                "We build custom AI agents for business process automation, document analysis, and customer support. "
                "Our team of 45 engineers has expertise in machine learning, computer vision, and conversational AI. "
                "We serve clients in fintech, healthcare, and retail sectors."
            ),
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
                    name="Cybersecurity",
                    sub_domains=["Threat Detection", "SOC Operations"],
                    level=DomainLevel.EXPERT,
                ),
                Domain(
                    name="Process Automation",
                    sub_domains=["RPA", "Workflow Automation"],
                    level=DomainLevel.INTERMEDIATE,
                ),
            ],
        )
    )

    # Validate with LLM
    api_key = os.getenv("OPENAI_API_KEY")
    validator = InputValidator(openai_api_key=api_key)
    result = validator.validate(company_input)

    print("=== LLM Validation Example ===")
    print(f"Is Valid: {result.is_valid}")
    print(f"Score: {result.score}/10")
    print(f"Missing Fields: {result.missing_fields}")
    print(f"Reason: {result.reason}")
    print()


def example_invalid_input():
    """Example with missing fields."""

    # Create an incomplete company profile
    company_input = CompanyInput(
        company=CompanyProfile(
            name="A",  # Too short
            description="Short",  # Less than 20 chars
            type="SME",
            employees=0,  # Invalid
            country="",  # Missing
            domains=[],  # Empty
        )
    )

    validator = InputValidator()
    result = validator.validate(company_input)

    print("=== Invalid Input Example ===")
    print(f"Is Valid: {result.is_valid}")
    print(f"Score: {result.score}/10")
    print(f"Missing Fields: {result.missing_fields}")
    print(f"Reason: {result.reason}")
    print()


if __name__ == "__main__":
    print("EU Call Finder - Input Validator Examples\n")

    # Run examples
    example_basic_validation()
    example_invalid_input()

    # Only run LLM example if API key is available
    if os.getenv("OPENAI_API_KEY"):
        example_with_llm()
    else:
        print("=== LLM Validation Example ===")
        print("Skipped: OPENAI_API_KEY not found in environment variables.")
        print("Set OPENAI_API_KEY to enable LLM validation.")
