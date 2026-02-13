"""
Input Validator for EU Call Finder.
Validates user input using both basic checks and LLM semantic analysis.
Uses manual OpenAI client (v1.0+).
"""

import os
import json
from typing import List

from contracts.schemas import CompanyInput, ValidationResult


class InputValidator:
    """
    Validates user input describing their company.
    Uses basic validation + LLM semantic analysis to ensure company data is adequate.
    """

    def __init__(self, openai_api_key: str = None, model: str = None):
        """
        Initialize the input validator.

        Args:
            openai_api_key: OpenAI API key. If None, reads from OPENAI_API_KEY env var.
            model: OpenAI model to use for validation. If None, reads from OPENAI_MODEL env var (defaults to gpt-3.5-turbo).
        """
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    def validate(self, input_data: CompanyInput) -> ValidationResult:
        """
        Validate the company input data.

        Args:
            input_data: The company input data to validate

        Returns:
            ValidationResult with validation status and feedback
        """
        # Step 1: Basic Validation
        basic_result = self._basic_validation(input_data)
        if not basic_result.is_valid:
            return basic_result

        # Step 2: LLM Validation (only if API key is available)
        if self.openai_api_key:
            try:
                llm_result = self._llm_validation(input_data)
                return self._merge_results(basic_result, llm_result)
            except Exception as e:
                # If LLM fails, return basic result with warning
                return ValidationResult(
                    is_valid=basic_result.is_valid,
                    score=basic_result.score,
                    missing_fields=basic_result.missing_fields,
                    reason=f"{basic_result.reason} (Note: LLM validation failed: {str(e)})",
                )

        return basic_result

    def _basic_validation(self, input_data: CompanyInput) -> ValidationResult:
        """
        Perform basic structural validation.
        Only checks required fields: name, type, employees, country, domains, description.
        Does NOT check for keywords or search_params (they are optional).

        Args:
            input_data: The input data to validate

        Returns:
            Basic validation result
        """
        missing_fields: List[str] = []

        # Check company name
        if not input_data.company.name or len(input_data.company.name.strip()) < 2:
            missing_fields.append("company.name")

        # Check company description (must be at least 20 characters)
        if (
            not input_data.company.description
            or len(input_data.company.description.strip()) < 20
        ):
            missing_fields.append("company.description (minimum 20 characters)")

        # Check company type
        if not input_data.company.type:
            missing_fields.append("company.type")

        # Check employees
        if input_data.company.employees < 1:
            missing_fields.append("company.employees")

        # Check country
        if not input_data.company.country:
            missing_fields.append("company.country")

        # Check domains (at least one required)
        if not input_data.company.domains or len(input_data.company.domains) == 0:
            missing_fields.append("company.domains (at least one domain required)")
        else:
            # Check each domain has a name
            for i, domain in enumerate(input_data.company.domains):
                if not domain.name or len(domain.name.strip()) < 1:
                    missing_fields.append(f"company.domains[{i}].name")

        # NOTE: We intentionally do NOT check for keywords or search_params
        # They are optional and will be inferred by the Planner

        if missing_fields:
            return ValidationResult(
                is_valid=False,
                score=0.0,
                missing_fields=missing_fields,
                reason=f"Missing required fields: {', '.join(missing_fields)}",
            )

        # Calculate basic score based on description quality
        score = 5.0  # Base score for passing basic validation

        # Bonus for longer, more detailed description
        desc_length = len(input_data.company.description.strip())
        if desc_length >= 100:
            score += 2.0
        elif desc_length >= 50:
            score += 1.0

        # Bonus for multiple domains
        if len(input_data.company.domains) >= 2:
            score += 1.0

        # Bonus for detailed domains (with sub_domains)
        detailed_domains = sum(1 for d in input_data.company.domains if d.sub_domains)
        if detailed_domains >= 1:
            score += 1.0

        return ValidationResult(
            is_valid=True,
            score=min(10.0, round(score, 1)),
            missing_fields=[],
            reason="Basic validation passed. Semantic analysis will provide detailed assessment.",
        )

    def _llm_validation(self, input_data: CompanyInput) -> ValidationResult:
        """
        Perform semantic validation using OpenAI LLM.

        Args:
            input_data: The input data to validate

        Returns:
            LLM-based validation result
        """
        prompt = self._create_validation_prompt(input_data)

        # Call OpenAI API using v1.0+ syntax
        import openai

        client = openai.OpenAI(
            api_key=self.openai_api_key, base_url=self.openai_base_url
        )

        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert validator for EU funding applications. Analyze company descriptions for specificity and relevance to EU funding calls.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=500,
        )

        # Parse the response
        content = response.choices[0].message.content
        return self._parse_llm_response(content)

    def _create_validation_prompt(self, input_data: CompanyInput) -> str:
        """
        Create a prompt for LLM validation.

        Args:
            input_data: The input data to validate

        Returns:
            Formatted prompt string
        """
        domains_str = "\n".join(
            [
                f"  - {d.name} (level: {d.level.value})"
                f"{' - Sub-domains: ' + ', '.join(d.sub_domains) if d.sub_domains else ''}"
                for d in input_data.company.domains
            ]
        )

        prompt = f"""Analyze this company description for EU funding suitability.

Company Information:
- Name: {input_data.company.name}
- Type: {input_data.company.type}
- Employees: {input_data.company.employees}
- Country: {input_data.company.country}
- City: {input_data.company.city or "Not specified"}

Description:
{input_data.company.description}

Domains of Expertise:
{domains_str}

Your task:
1. Evaluate if the company description is SPECIFIC enough to find relevant EU funding calls
2. Check if it describes actual activities, technologies, and competencies (not just generic statements)
3. Assess whether the description provides actionable information for matching with EU programs

Scoring:
- 0-3: Too vague/generic, cannot match with funding calls
- 4-5: Somewhat specific but lacks detail
- 6-7: Good level of detail, describes actual activities
- 8-10: Excellent, highly specific with clear technologies and competencies

Return ONLY a JSON object with this structure:
{{
    "is_valid": true/false,
    "score": 0-10,
    "missing_fields": ["list what information is missing or too vague"],
    "reason": "explanation of the score and specific recommendations"
}}

Be strict: Generic statements like 'we are a tech company' or 'we do software development' without specifics should score low."""

        return prompt

    def _parse_llm_response(self, response: str) -> ValidationResult:
        """
        Parse LLM response into ValidationResult.

        Args:
            response: The LLM response string

        Returns:
            Parsed validation result
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                json_str = response.split("```")[1].strip()
            else:
                json_str = response.strip()

            data = json.loads(json_str)

            return ValidationResult(
                is_valid=data.get("is_valid", True),
                score=float(data.get("score", 5.0)),
                missing_fields=data.get("missing_fields", []),
                reason=data.get("reason", "LLM validation completed"),
            )

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            # If parsing fails, return a default result
            return ValidationResult(
                is_valid=True,
                score=5.0,
                missing_fields=[],
                reason=f"Could not parse LLM response: {str(e)}. Using fallback validation.",
            )

    def _merge_results(
        self, basic: ValidationResult, llm: ValidationResult
    ) -> ValidationResult:
        """
        Merge basic and LLM validation results.
        LLM score takes precedence, but both must pass for is_valid.

        Args:
            basic: Basic validation result
            llm: LLM validation result

        Returns:
            Merged validation result
        """
        # Combine missing fields
        all_missing = list(set(basic.missing_fields + llm.missing_fields))

        # Valid only if both pass
        is_valid = basic.is_valid and llm.is_valid and llm.score >= 4.0

        # Use LLM score primarily, but cap at basic score if LLM is too generous
        final_score = min(llm.score, basic.score + 2.0)

        # Merge reasons
        if basic.is_valid:
            reason = f"LLM Analysis: {llm.reason}"
        else:
            reason = basic.reason

        return ValidationResult(
            is_valid=is_valid,
            score=round(final_score, 1),
            missing_fields=all_missing,
            reason=reason,
        )


# Convenience function for direct use
def validate_company_input(
    input_data: CompanyInput, openai_api_key: str = None
) -> ValidationResult:
    """
    Validate company input data.

    Args:
        input_data: The company input to validate
        openai_api_key: Optional OpenAI API key

    Returns:
        ValidationResult with validation status
    """
    validator = InputValidator(openai_api_key=openai_api_key)
    return validator.validate(input_data)
