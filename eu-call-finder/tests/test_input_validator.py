"""
Tests for Input Validator.
"""

import pytest
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contracts.schemas import CompanyInput, CompanyProfile, Domain, DomainLevel
from safety.input_validator import InputValidator


class TestBasicValidation:
    """Tests for basic validation without LLM."""

    def test_valid_input_passes(self):
        """Test that a valid company profile passes validation."""
        input_data = CompanyInput(
            company=CompanyProfile(
                name="TechStart BG",
                description="We are a startup company that builds innovative software solutions for businesses in the fintech sector.",
                type="SME",
                employees=15,
                country="Bulgaria",
                domains=[
                    Domain(
                        name="Software Development",
                        sub_domains=["Web Applications"],
                        level=DomainLevel.ADVANCED,
                    )
                ],
            )
        )

        validator = InputValidator()
        result = validator.validate(input_data)

        assert result.is_valid is True
        assert result.score >= 5.0
        assert len(result.missing_fields) == 0

    def test_missing_name_fails(self):
        """Test that missing company name fails validation."""
        input_data = CompanyInput(
            company=CompanyProfile(
                name="",
                description="We are a startup company that builds software solutions.",
                type="SME",
                employees=15,
                country="Bulgaria",
                domains=[
                    Domain(
                        name="Software Development",
                        sub_domains=[],
                        level=DomainLevel.ADVANCED,
                    )
                ],
            )
        )

        validator = InputValidator()
        result = validator.validate(input_data)

        assert result.is_valid is False
        assert "company.name" in result.missing_fields

    def test_short_description_fails(self):
        """Test that description less than 20 characters fails."""
        input_data = CompanyInput(
            company=CompanyProfile(
                name="TechStart",
                description="Short desc",  # Less than 20 chars
                type="SME",
                employees=15,
                country="Bulgaria",
                domains=[
                    Domain(name="Software", sub_domains=[], level=DomainLevel.BEGINNER)
                ],
            )
        )

        validator = InputValidator()
        result = validator.validate(input_data)

        assert result.is_valid is False
        assert any("description" in field.lower() for field in result.missing_fields)

    def test_missing_country_fails(self):
        """Test that missing country fails validation."""
        input_data = CompanyInput(
            company=CompanyProfile(
                name="TechStart",
                description="We are a startup company that builds software solutions for businesses.",
                type="SME",
                employees=15,
                country="",
                domains=[
                    Domain(name="Software", sub_domains=[], level=DomainLevel.BEGINNER)
                ],
            )
        )

        validator = InputValidator()
        result = validator.validate(input_data)

        assert result.is_valid is False
        assert "company.country" in result.missing_fields

    def test_zero_employees_fails(self):
        """Test that zero employees fails validation."""
        input_data = CompanyInput(
            company=CompanyProfile(
                name="TechStart",
                description="We are a startup company that builds software solutions.",
                type="SME",
                employees=0,
                country="Bulgaria",
                domains=[
                    Domain(name="Software", sub_domains=[], level=DomainLevel.BEGINNER)
                ],
            )
        )

        validator = InputValidator()
        result = validator.validate(input_data)

        assert result.is_valid is False
        assert "company.employees" in result.missing_fields

    def test_empty_domains_fails(self):
        """Test that empty domains list fails validation."""
        input_data = CompanyInput(
            company=CompanyProfile(
                name="TechStart",
                description="We are a startup company that builds software solutions.",
                type="SME",
                employees=15,
                country="Bulgaria",
                domains=[],
            )
        )

        validator = InputValidator()
        result = validator.validate(input_data)

        assert result.is_valid is False
        assert any("domains" in field.lower() for field in result.missing_fields)

    def test_detailed_description_gets_higher_score(self):
        """Test that detailed descriptions get higher scores."""
        short_desc_input = CompanyInput(
            company=CompanyProfile(
                name="TechStart",
                description="We build software solutions for businesses.",  # ~50 chars
                type="SME",
                employees=15,
                country="Bulgaria",
                domains=[
                    Domain(name="Software", sub_domains=[], level=DomainLevel.BEGINNER)
                ],
            )
        )

        long_desc_input = CompanyInput(
            company=CompanyProfile(
                name="TechStart",
                description="We are an innovative software development company specializing in building enterprise-grade applications using cutting-edge technologies like AI, machine learning, and cloud computing. Our team of experts delivers custom solutions.",  # >100 chars
                type="SME",
                employees=15,
                country="Bulgaria",
                domains=[
                    Domain(
                        name="Software",
                        sub_domains=["AI", "Cloud"],
                        level=DomainLevel.EXPERT,
                    )
                ],
            )
        )

        validator = InputValidator()
        short_result = validator.validate(short_desc_input)
        long_result = validator.validate(long_desc_input)

        assert long_result.score > short_result.score

    def test_multiple_domains_increases_score(self):
        """Test that multiple domains increase the score."""
        single_domain_input = CompanyInput(
            company=CompanyProfile(
                name="TechStart",
                description="We build software solutions for businesses in various sectors.",
                type="SME",
                employees=15,
                country="Bulgaria",
                domains=[
                    Domain(name="Software", sub_domains=[], level=DomainLevel.ADVANCED)
                ],
            )
        )

        multi_domain_input = CompanyInput(
            company=CompanyProfile(
                name="TechStart",
                description="We build software solutions for businesses in various sectors.",
                type="SME",
                employees=15,
                country="Bulgaria",
                domains=[
                    Domain(name="Software", sub_domains=[], level=DomainLevel.ADVANCED),
                    Domain(
                        name="AI",
                        sub_domains=["Machine Learning"],
                        level=DomainLevel.EXPERT,
                    ),
                ],
            )
        )

        validator = InputValidator()
        single_result = validator.validate(single_domain_input)
        multi_result = validator.validate(multi_domain_input)

        assert multi_result.score > single_result.score

    def test_optional_keywords_not_checked(self):
        """Test that optional keywords field is not validated."""
        # This should pass even without keywords (they're optional)
        input_data = CompanyInput(
            company=CompanyProfile(
                name="TechStart",
                description="We are a startup company that builds software solutions.",
                type="SME",
                employees=15,
                country="Bulgaria",
                domains=[
                    Domain(name="Software", sub_domains=[], level=DomainLevel.BEGINNER)
                ],
            )
            # Note: keywords and search_params are not provided
        )

        validator = InputValidator()
        result = validator.validate(input_data)

        # Should pass because keywords are optional
        assert result.is_valid is True


class TestScoreCalculation:
    """Tests for score calculation logic."""

    def test_minimum_passing_score(self):
        """Test that minimum passing score is 5.0."""
        input_data = CompanyInput(
            company=CompanyProfile(
                name="TechStart",
                description="We build software solutions.",  # Short description
                type="SME",
                employees=15,
                country="Bulgaria",
                domains=[
                    Domain(name="Software", sub_domains=[], level=DomainLevel.BEGINNER)
                ],
            )
        )

        validator = InputValidator()
        result = validator.validate(input_data)

        # Should be valid but with low score
        assert result.is_valid is True
        assert result.score >= 5.0
        assert result.score < 7.0

    def test_maximum_score_is_ten(self):
        """Test that maximum score is capped at 10."""
        input_data = CompanyInput(
            company=CompanyProfile(
                name="NexGen AI Solutions",
                description="We are a leading AI company specializing in natural language processing, computer vision, and machine learning solutions. We have extensive experience in developing enterprise-grade AI applications for Fortune 500 companies across healthcare, finance, and retail sectors. Our team of 50+ researchers and engineers has published 20+ papers in top-tier conferences.",
                type="SME",
                employees=50,
                country="Germany",
                city="Berlin",
                domains=[
                    Domain(
                        name="Artificial Intelligence",
                        sub_domains=[
                            "NLP",
                            "Computer Vision",
                            "Machine Learning",
                            "Deep Learning",
                        ],
                        level=DomainLevel.EXPERT,
                    ),
                    Domain(
                        name="Data Science",
                        sub_domains=["Big Data", "Analytics"],
                        level=DomainLevel.EXPERT,
                    ),
                    Domain(
                        name="Cloud Computing",
                        sub_domains=["AWS", "Azure"],
                        level=DomainLevel.ADVANCED,
                    ),
                ],
            )
        )

        validator = InputValidator()
        result = validator.validate(input_data)

        assert result.score <= 10.0


class TestEdgeCases:
    """Tests for edge cases."""

    def test_name_with_minimum_length(self):
        """Test that 2-character name passes."""
        input_data = CompanyInput(
            company=CompanyProfile(
                name="AB",  # Exactly 2 characters
                description="We are a startup company that builds software solutions.",
                type="SME",
                employees=15,
                country="Bulgaria",
                domains=[
                    Domain(name="Software", sub_domains=[], level=DomainLevel.BEGINNER)
                ],
            )
        )

        validator = InputValidator()
        result = validator.validate(input_data)

        assert result.is_valid is True

    def test_unicode_characters(self):
        """Test that unicode characters are handled properly."""
        input_data = CompanyInput(
            company=CompanyProfile(
                name="ТехСтарт БГ",  # Cyrillic
                description="Ние сме софтуерна компания, която разработва иновативни решения за бизнеса.",
                type="SME",
                employees=15,
                country="Bulgaria",
                domains=[
                    Domain(
                        name="Софтуерна разработка",
                        sub_domains=["Уеб приложения"],
                        level=DomainLevel.ADVANCED,
                    )
                ],
            )
        )

        validator = InputValidator()
        result = validator.validate(input_data)

        assert result.is_valid is True

    def test_domain_without_subdomains(self):
        """Test that domain without subdomains is valid."""
        input_data = CompanyInput(
            company=CompanyProfile(
                name="TechStart",
                description="We are a startup company that builds software solutions.",
                type="SME",
                employees=15,
                country="Bulgaria",
                domains=[
                    Domain(
                        name="Software",
                        sub_domains=[],  # Empty subdomains
                        level=DomainLevel.BEGINNER,
                    )
                ],
            )
        )

        validator = InputValidator()
        result = validator.validate(input_data)

        assert result.is_valid is True

    def test_city_is_optional(self):
        """Test that city field is optional."""
        input_data = CompanyInput(
            company=CompanyProfile(
                name="TechStart",
                description="We are a startup company that builds software solutions.",
                type="SME",
                employees=15,
                country="Bulgaria",
                city=None,  # Not provided
                domains=[
                    Domain(name="Software", sub_domains=[], level=DomainLevel.BEGINNER)
                ],
            )
        )

        validator = InputValidator()
        result = validator.validate(input_data)

        assert result.is_valid is True


class TestLLMValidation:
    """Tests for LLM validation (requires OPENAI_API_KEY)."""

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set"
    )
    def test_llm_validates_description_quality(self):
        """Test that LLM evaluates description quality."""
        # Generic description (should get lower score)
        generic_input = CompanyInput(
            company=CompanyProfile(
                name="Tech Company",
                description="We are a tech company that does software stuff.",
                type="SME",
                employees=10,
                country="USA",
                domains=[
                    Domain(
                        name="Technology", sub_domains=[], level=DomainLevel.BEGINNER
                    )
                ],
            )
        )

        validator = InputValidator()
        result = validator.validate(generic_input)

        # LLM should flag this as too generic
        assert result.score < 7.0

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set"
    )
    def test_llm_recognizes_specific_description(self):
        """Test that LLM recognizes specific, detailed descriptions."""
        specific_input = CompanyInput(
            company=CompanyProfile(
                name="DeepMind Medical",
                description="We develop AI-powered diagnostic tools for radiology, specializing in computer vision algorithms for detecting early-stage tumors in CT scans and MRI images. Our FDA-approved solutions are used by 200+ hospitals across Europe.",
                type="SME",
                employees=45,
                country="UK",
                domains=[
                    Domain(
                        name="Medical AI",
                        sub_domains=["Computer Vision", "Diagnostic Imaging"],
                        level=DomainLevel.EXPERT,
                    )
                ],
            )
        )

        validator = InputValidator()
        result = validator.validate(specific_input)

        # LLM should recognize this as specific and high-quality
        assert result.score >= 7.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
