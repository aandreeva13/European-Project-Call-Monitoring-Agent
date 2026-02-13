def apply_eligibility_filters(call_data: dict, company_profile: dict) -> dict:
    """
    Apply hard eligibility filters to determine if company can apply.
    Checks: organization type, country, budget range, TRL level, consortium requirements.
    """

    # Check organization type eligibility
    type_ok = check_organization_type(call_data, company_profile)

    # Check country eligibility
    country_ok = check_country_eligibility(call_data, company_profile)

    # Check budget eligibility
    budget_ok = check_budget_eligibility(call_data, company_profile)

    # Check TRL level compatibility
    trl_ok = check_trl_compatibility(call_data, company_profile)

    # Check consortium feasibility
    consortium_ok = check_consortium_feasibility(call_data, company_profile)

    # Check if SME participation is encouraged/required
    sme_status = check_sme_status(call_data, company_profile)

    all_passed = all([type_ok, country_ok, budget_ok, trl_ok, consortium_ok])

    return {
        "type_ok": type_ok,
        "country_ok": country_ok,
        "budget_ok": budget_ok,
        "trl_ok": trl_ok,
        "consortium_ok": consortium_ok,
        "sme_encouraged": sme_status["encouraged"],
        "sme_required": sme_status["required"],
        "all_passed": all_passed,
        "details": {
            "type_message": get_type_message(type_ok, call_data, company_profile),
            "country_message": get_country_message(country_ok, company_profile),
            "budget_message": get_budget_message(budget_ok, call_data, company_profile),
            "trl_message": get_trl_message(trl_ok, call_data, company_profile),
            "consortium_message": get_consortium_message(
                consortium_ok, call_data, company_profile
            ),
        },
    }


def check_organization_type(call_data: dict, company_profile: dict) -> bool:
    """Check if company type is eligible for this call."""
    eligible_types = call_data.get("eligible_organization_types", [])
    company_type = company_profile.get("type", "").upper()

    if not eligible_types:
        return True  # No restrictions specified

    eligible_types_upper = [t.upper() for t in eligible_types]

    type_mapping = {
        "SME": ["SME", "SMALL", "MEDIUM", "SMALL AND MEDIUM ENTERPRISE", "МСП"],
        "SMALL": ["SME", "SMALL"],
        "MEDIUM": ["SME", "MEDIUM"],
        "LARGE": ["LARGE", "BIG ENTERPRISE", "ГОЛЯМО"],
        "UNIVERSITY": ["UNIVERSITY", "ACADEMIC", "RESEARCH", "УНИВЕРСИТЕТ"],
        "RESEARCH INSTITUTE": ["RESEARCH", "INSTITUTE", "ACADEMIC", "ИНСТИТУТ"],
        "NGO": ["NGO", "NON-PROFIT", "НПО"],
        "PUBLIC": ["PUBLIC", "GOVERNMENT", "ДЪРЖАВЕН"],
        "CLUSTER": ["CLUSTER", "КЛЪСТЕР"],
    }

    for eligible in eligible_types_upper:
        if company_type == eligible:
            return True
        if eligible in type_mapping.get(company_type, []):
            return True

    return False


def check_country_eligibility(call_data: dict, company_profile: dict) -> bool:
    """Check if company country is eligible for this call."""
    eligible_countries = call_data.get("eligible_countries", [])
    company_country = company_profile.get("country", "")

    if not eligible_countries:
        return True  # No restrictions, assume all EU/associated countries

    # Standardize country names
    company_country_normalized = company_country.lower().strip()
    eligible_normalized = [c.lower().strip() for c in eligible_countries]

    eu_countries = [
        "austria",
        "belgium",
        "bulgaria",
        "croatia",
        "cyprus",
        "czech republic",
        "czechia",
        "denmark",
        "estonia",
        "finland",
        "france",
        "germany",
        "greece",
        "hungary",
        "ireland",
        "italy",
        "latvia",
        "lithuania",
        "luxembourg",
        "malta",
        "netherlands",
        "poland",
        "portugal",
        "romania",
        "slovakia",
        "slovenia",
        "spain",
        "sweden",
    ]

    # Check if company country is in eligible list
    if company_country_normalized in eligible_normalized:
        return True

    # Check if "EU" or "all" is in eligible
    if any(
        x in eligible_normalized
        for x in ["eu", "european union", "all", "all member states"]
    ):
        if (
            company_country_normalized in eu_countries
            or "bulgaria" in company_country_normalized
        ):
            return True

    return False


def check_budget_eligibility(call_data: dict, company_profile: dict) -> bool:
    """Check if call budget is within feasible range for company."""
    call_budget = call_data.get("budget_per_project", {})
    search_params = company_profile.get("search_params", {})
    preferred_range = search_params.get("budget_range", {})

    if not call_budget or not preferred_range:
        return True  # No specific requirements

    call_min = call_budget.get("min", 0)
    call_max = call_budget.get("max", float("inf"))

    pref_min = preferred_range.get("min", 0)
    pref_max = preferred_range.get("max", float("inf"))

    # Check if there's any overlap between call budget and preferred range
    if call_max < pref_min or call_min > pref_max:
        # Call budget is completely outside preferred range
        # Allow if within 50% of range
        if call_max < pref_min * 0.5 or call_min > pref_max * 2:
            return False

    return True


def check_trl_compatibility(call_data: dict, company_profile: dict) -> bool:
    """Check if TRL levels are compatible."""
    call_trl = call_data.get("trl", "")
    company_domains = company_profile.get("domains", [])

    if not call_trl:
        return True  # No TRL requirement specified

    # Parse TRL range (e.g., "4-7" or "6")
    try:
        if "-" in str(call_trl):
            call_trl_min, call_trl_max = map(int, str(call_trl).split("-"))
        else:
            call_trl_min = call_trl_max = int(call_trl)
    except (ValueError, TypeError):
        return True  # Cannot parse, assume ok

    # Assume company can work in TRL 4-8 range for their domains
    company_trl_min = 4
    company_trl_max = 8

    # Check overlap
    if call_trl_max < company_trl_min or call_trl_min > company_trl_max:
        return False

    return True


def check_consortium_feasibility(call_data: dict, company_profile: dict) -> bool:
    """Check if consortium requirements are feasible."""
    consortium = call_data.get("consortium", {})
    min_partners = consortium.get("min_partners", 1)
    min_countries = consortium.get("min_countries", 1)

    # Single company can always apply if min_partners is 1
    if min_partners == 1:
        return True

    # For multi-partner requirements, check if company has experience
    past_projects = company_profile.get("past_eu_projects", [])

    # If they've done EU projects before, assume they can form consortium
    if len(past_projects) > 0:
        return True

    # Check company size - larger companies might have better network
    employees = company_profile.get("employees", 0)
    if employees >= 50 and min_partners <= 5:
        return True

    # If requirements are very high
    if min_partners > 10 or min_countries > 5:
        return False

    return True  # Assume feasible with effort


def check_sme_status(call_data: dict, company_profile: dict) -> dict:
    """Check SME participation status."""
    funding_rate = call_data.get("funding_rate", "").lower()
    company_type = company_profile.get("type", "").upper()

    is_sme = company_type in ["SME", "SMALL", "MEDIUM"]

    encouraged = False
    required = False

    if "sme" in funding_rate:
        if "encouraged" in funding_rate or "preference" in funding_rate:
            encouraged = True
        if "required" in funding_rate or "mandatory" in funding_rate:
            required = True
        if "70%" in funding_rate or "high" in funding_rate:
            encouraged = True

    return {"is_sme": is_sme, "encouraged": encouraged and is_sme, "required": required}


def get_type_message(passed: bool, call_data: dict, company_profile: dict) -> str:
    """Generate message for type check."""
    if passed:
        return f"Organization type '{company_profile.get('type')}' is eligible"
    else:
        return f"Organization type '{company_profile.get('type')}' may not be eligible"


def get_country_message(passed: bool, company_profile: dict) -> str:
    """Generate message for country check."""
    if passed:
        return f"Country '{company_profile.get('country')}' is eligible"
    else:
        return f"Country '{company_profile.get('country')}' may not be eligible"


def get_budget_message(passed: bool, call_data: dict, company_profile: dict) -> str:
    """Generate message for budget check."""
    budget = call_data.get("budget_per_project", {})
    if passed:
        return f"Budget range {budget.get('min', 'N/A')}-{budget.get('max', 'N/A')} EUR is feasible"
    else:
        return f"Budget may be outside preferred range"


def get_trl_message(passed: bool, call_data: dict, company_profile: dict) -> str:
    """Generate message for TRL check."""
    trl = call_data.get("trl", "N/A")
    if passed:
        return f"TRL {trl} is compatible with company capabilities"
    else:
        return f"TRL {trl} may not align with company experience"


def get_consortium_message(passed: bool, call_data: dict, company_profile: dict) -> str:
    """Generate message for consortium check."""
    consortium = call_data.get("consortium", {})
    min_partners = consortium.get("min_partners", 1)

    if min_partners == 1:
        return "Single applicant allowed"
    elif passed:
        return f"Consortium of {min_partners}+ partners is feasible"
    else:
        return f"Consortium of {min_partners}+ partners may be challenging"
