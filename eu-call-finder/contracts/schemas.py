"""
Contract schemas for EU Call Finder.
Defines Pydantic models for input/output data validation.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class DomainLevel(str, Enum):
    """Expertise levels for domains."""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class Domain(BaseModel):
    """Domain of expertise with sub-domains and level."""

    name: str = Field(
        ..., description="Main domain name (e.g., 'Artificial Intelligence')"
    )
    sub_domains: List[str] = Field(
        default=[], description="Sub-domains or specializations"
    )
    level: DomainLevel = Field(..., description="Expertise level in this domain")


class CompanyProfile(BaseModel):
    """Company profile information - the core input from the user."""

    name: str = Field(..., min_length=2, description="Company name")
    description: str = Field(
        ...,
        min_length=20,
        description="Detailed company description with activities and technologies",
    )
    type: Literal[
        "SME", "Large Enterprise", "NGO", "University", "Public Body", "Other"
    ] = Field(..., description="Type of organization")
    employees: int = Field(..., ge=1, description="Number of employees")
    country: str = Field(
        ..., min_length=2, description="Country where the company is based"
    )
    city: Optional[str] = Field(None, description="City where the company is located")
    domains: List[Domain] = Field(
        ..., min_length=1, description="Areas of expertise and competence"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "NexGen AI Solutions",
                "description": "Bulgarian AI company developing intelligent automation solutions for enterprise clients. Specialized in LLM applications, agentic AI and NLP.",
                "type": "SME",
                "employees": 45,
                "country": "Bulgaria",
                "city": "Sofia",
                "domains": [
                    {
                        "name": "Artificial Intelligence",
                        "sub_domains": ["Machine Learning", "NLP", "Agentic AI"],
                        "level": "advanced",
                    },
                    {
                        "name": "Cybersecurity",
                        "sub_domains": ["Threat Detection", "SOC"],
                        "level": "expert",
                    },
                ],
            }
        }
    )


class CompanyInput(BaseModel):
    """
    Root input model for company search.
    Only company profile is required - keywords and search_params are optional
    and will be inferred by the Planner.
    """

    company: CompanyProfile = Field(..., description="Company profile information")
    command: Optional[str] = Field(None, description="Optional command description")
    keywords: Optional[List[str]] = Field(
        None,
        description="Optional keywords - will be inferred by Planner if not provided",
    )
    search_params: Optional[dict] = Field(
        None,
        description="Optional search parameters - will be inferred by Planner if not provided",
    )


class ValidationResult(BaseModel):
    """Result of input validation."""

    is_valid: bool = Field(..., description="Whether the input is valid")
    score: float = Field(
        ..., ge=0, le=10, description="Quality score of the input (0-10)"
    )
    missing_fields: List[str] = Field(
        default=[], description="List of missing or inadequate fields"
    )
    reason: str = Field(..., description="Explanation of the validation result")
