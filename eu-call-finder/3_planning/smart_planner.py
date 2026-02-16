"""
Smart Planner - Advanced company analysis with LLM-enhanced query generation.
Maintains compatibility with existing scraper while providing deeper analysis.
"""

import re
import json
import os
from typing import List, Dict, Any, Optional
from collections import Counter

# HARDCODED filter configuration for EU Funding Portal API compatibility
STATIC_FILTER_CONFIG = {
    "bool": {
        "must": [
            {"terms": {"type": ["1", "8"]}},  # Grants & Prizes
            {"terms": {"status": ["31094501", "31094502"]}},  # Open & Forthcoming
            {"term": {"programmePeriod": "2021 - 2027"}},
        ]
    }
}


class SmartPlanner:
    """
    Advanced planner that deeply analyzes company profiles and uses LLM for query generation.
    Maintains backward compatibility with existing scraper.
    """

    def __init__(self, openai_api_key: str = None, model: str = None):
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    def analyze_company_deep(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep analysis of company profile.
        Extracts technologies, applications, competencies, and EU alignment.
        """
        company = company_data.get("company", {})
        description = company.get("description", "").lower()
        domains = company.get("domains", [])

        # Store ALL company fields for LLM analysis
        analysis = {
            "name": company.get("name"),
            "type": company.get("type"),
            "country": company.get("country"),
            "employees": company.get("employees"),
            "full_description": company.get("description", ""),
            "website": company.get("website"),
            "founded_year": company.get("founded_year"),
            "revenue": company.get("revenue"),
            "certifications": company.get("certifications", []),
            "partnerships": company.get("partnerships", []),
            "previous_projects": company.get("previous_projects", []),
            "contact_email": company.get("contact_email"),
            "contact_phone": company.get("contact_phone"),
            "address": company.get("address"),
            "registration_number": company.get("registration_number"),
            "vat_number": company.get("vat_number"),
            "technologies": [],
            "applications": [],
            "competencies": [],
            "keywords": [],
            "eu_programs": [],
            "trl_level": None,
            "budget_range": None,
            "raw_company_data": company,  # Include complete raw data
        }

        # Extract core technologies from description
        tech_patterns = {
            "artificial intelligence": [
                "AI",
                "machine learning",
                "deep learning",
                "neural networks",
                "NLP",
            ],
            "computer vision": [
                "image recognition",
                "medical imaging",
                "visual analytics",
            ],
            "data analytics": ["big data", "predictive analytics", "data mining"],
            "cloud computing": ["cloud", "SaaS", "distributed systems"],
            "cybersecurity": ["security", "encryption", "threat detection"],
            "robotics": ["automation", "robotics", "autonomous systems"],
            "biotechnology": ["biotech", "genomics", "molecular biology"],
            "blockchain": ["blockchain", "distributed ledger", "Web3"],
            "IoT": ["internet of things", "sensors", "connected devices"],
            "quantum": ["quantum computing", "quantum algorithms"],
        }

        for tech, synonyms in tech_patterns.items():
            if any(word in description for word in [tech] + synonyms):
                analysis["technologies"].append(tech)
                analysis["keywords"].extend(synonyms[:2])

        # Extract application domains
        app_areas = {
            "healthcare": [
                "medical",
                "clinical",
                "patient",
                "diagnostics",
                "therapeutics",
                "pharma",
            ],
            "education": ["learning", "training", "education", "e-learning"],
            "transport": ["mobility", "logistics", "transport", "automotive"],
            "agriculture": ["farming", "agriculture", "agritech", "food"],
            "manufacturing": ["industry", "factory", "production", " Industry 4.0"],
            "finance": ["fintech", "banking", "insurance", "financial"],
            "energy": ["renewable", "solar", "wind", "smart grid", "clean energy"],
            "environment": ["climate", "sustainability", "carbon", "green"],
            "security": ["defense", "security", "safety", "protection"],
            "space": ["space", "satellite", "aerospace"],
        }

        for app, keywords in app_areas.items():
            if any(word in description for word in keywords):
                analysis["applications"].append(app)

        # Extract from domains structure
        for domain in domains:
            domain_name = domain.get("name", "").lower()
            sub_domains = domain.get("sub_domains", [])
            level = domain.get("level", "intermediate")

            analysis["competencies"].append(
                {"domain": domain_name, "level": level, "specializations": sub_domains}
            )

            # Add domain and sub-domains to keywords
            analysis["keywords"].append(domain_name)
            analysis["keywords"].extend([s.lower() for s in sub_domains])

        # Determine EU programs based on analysis
        analysis["eu_programs"] = self._match_eu_programs(analysis)

        # Extract additional meaningful keywords
        analysis["keywords"] = self._extract_keywords(description, analysis["keywords"])

        # Estimate TRL level based on description
        analysis["trl_level"] = self._estimate_trl(description)

        # Estimate budget needs
        analysis["budget_range"] = self._estimate_budget(company)

        return analysis

    def _match_eu_programs(self, analysis: Dict) -> List[str]:
        """Match company focus to best EU funding programs."""
        programs = []
        techs = set(analysis.get("technologies", []))
        apps = set(analysis.get("applications", []))

        # Horizon Europe - Research & Innovation
        if any(
            t in techs
            for t in ["artificial intelligence", "biotechnology", "quantum", "robotics"]
        ):
            programs.append("Horizon Europe")

        # Digital Europe - Digital technologies
        if any(
            t in techs
            for t in [
                "artificial intelligence",
                "cybersecurity",
                "cloud computing",
                "data analytics",
            ]
        ):
            programs.append("Digital Europe")

        # EU4Health - Health
        if "healthcare" in apps or any(
            t in techs for t in ["biotechnology", "medical imaging"]
        ):
            programs.append("EU4Health")

        # LIFE Programme - Environment
        if (
            any(t in techs for t in ["renewable energy", "clean tech"])
            or "environment" in apps
        ):
            programs.append("LIFE Programme")

        # EIC Accelerator - SME innovation
        if analysis.get("type") == "SME" and len(programs) > 0:
            programs.append("EIC Accelerator")

        # Creative Europe - Cultural/creative
        if any(app in apps for app in ["culture", "media", "creative"]):
            programs.append("Creative Europe")

        # Erasmus+ - Education
        if "education" in apps:
            programs.append("Erasmus+")

        return programs if programs else ["Horizon Europe"]

    def _extract_keywords(self, description: str, existing: List[str]) -> List[str]:
        """Extract important keywords from description."""
        # Common stop words
        stop_words = {
            "the",
            "and",
            "for",
            "are",
            "with",
            "they",
            "this",
            "that",
            "have",
            "from",
            "been",
            "were",
            "said",
            "each",
            "which",
            "will",
            "about",
            "could",
            "would",
            "their",
            "there",
            "where",
        }

        # Extract meaningful words (4+ chars)
        words = re.findall(r"\b[a-zA-Z]{4,}\b", description.lower())
        words = [w for w in words if w not in stop_words and w not in existing]

        # Get most frequent words
        word_counts = Counter(words)
        top_words = [word for word, count in word_counts.most_common(8) if count >= 1]

        # Combine with existing, remove duplicates
        all_keywords = list(dict.fromkeys(existing + top_words))
        return all_keywords[:15]  # Limit to 15 keywords

    def _estimate_trl(self, description: str) -> int:
        """Estimate Technology Readiness Level from description."""
        trl_indicators = {
            9: ["commercial", "market ready", "deployed", "operational"],
            8: ["pilot", "demonstration", "field tested"],
            7: ["prototype", "system prototype", "integration"],
            6: ["validation", "model", "simulation"],
            5: ["laboratory", "component"],
            4: ["proof of concept", "proof-of-concept", "poc"],
            3: ["experimental", "proof of principle"],
            2: ["concept", "formulation", "design"],
            1: ["basic research", "fundamental"],
        }

        desc_lower = description.lower()
        for trl, indicators in sorted(trl_indicators.items(), reverse=True):
            if any(ind in desc_lower for ind in indicators):
                return trl
        return 5  # Default TRL

    def _estimate_budget(self, company: Dict) -> Dict[str, int]:
        """Estimate funding budget based on company size and type."""
        employees = company.get("employees", 10)

        if employees < 10:
            return {"min": 50000, "max": 300000, "typical": 150000}
        elif employees < 50:
            return {"min": 100000, "max": 1000000, "typical": 500000}
        elif employees < 250:
            return {"min": 500000, "max": 5000000, "typical": 2000000}
        else:
            return {"min": 1000000, "max": 10000000, "typical": 5000000}

    def generate_queries_with_llm(
        self, analysis: Dict, previous_feedback: str = None
    ) -> List[str]:
        """Use LLM to generate smart search queries based on deep analysis."""
        if not self.openai_api_key:
            # Fallback to rule-based if no LLM
            return self._generate_rule_based_queries(analysis, previous_feedback)

        try:
            import openai

            client = openai.OpenAI(
                api_key=self.openai_api_key, base_url=self.openai_base_url
            )

            # Build comprehensive prompt
            prompt = self._build_llm_prompt(analysis, previous_feedback)

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert EU funding search strategist. Generate precise Boolean search queries.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1000,
            )

            content = response.choices[0].message.content
            return self._parse_llm_queries(content)

        except Exception as e:
            print(f"[WARNING] LLM query generation failed: {e}")
            return self._generate_rule_based_queries(analysis, previous_feedback)

    def _build_llm_prompt(self, analysis: Dict, previous_feedback: str = None) -> str:
        """Build comprehensive prompt for LLM including ALL company data and feedback."""
        import json

        # Get raw company data - includes ALL fields from the original input
        raw_company = analysis.get("raw_company_data", {})

        prompt = f"""Based on this complete company profile, generate 5-6 targeted Boolean search queries for EU funding calls.

=== COMPLETE COMPANY INPUT (ALL DATA) ===
{json.dumps(raw_company, indent=2, default=str)}

=== EXTRACTED ANALYSIS ===
- Technologies: {", ".join(analysis.get("technologies", []))}
- Applications: {", ".join(analysis.get("applications", []))}
- Target EU Programs: {", ".join(analysis.get("eu_programs", []))}
- TRL Level: {analysis.get("trl_level")}
- Budget Range: {analysis.get("budget_range", {})}
- Keywords: {", ".join(analysis.get("keywords", []))}
"""

        if previous_feedback:
            prompt += f"""

=== PREVIOUS SEARCH FEEDBACK (ITERATION CONTEXT) ===
{previous_feedback}

=== INSTRUCTIONS FOR THIS ITERATION ===
You are in an iterative refinement process. The feedback above represents the cumulative learning from all previous iterations.
- Carefully analyze the feedback to understand what worked and what didn't
- Address ALL points mentioned in the feedback
- Generate queries that are more targeted and specific based on the feedback
- If feedback mentions specific domains, technologies, or requirements, prioritize those
"""

        prompt += """

CRITICAL RULES FOR QUERIES:
1. Generate SIMPLE KEYWORD QUERIES - the EU API does NOT support AND/OR operators
2. Use SPACE-separated keywords, NOT Boolean operators
3. Wrap multi-word concepts in quotes: "machine learning" healthcare
4. Keep queries SHORT (max 100 characters)
5. Each query should be 2-4 key terms maximum

EXAMPLES OF GOOD QUERIES:
- "machine learning" healthcare
- "artificial intelligence" Bulgaria
- "digital health" SME
- AI "medical imaging"
- healthcare innovation

BAD QUERIES (uses unsupported AND/OR):
- "machine learning" AND "healthcare"  <-- AND is NOT supported!
- "AI" OR "machine learning"          <-- OR is NOT supported!
- ("AI" OR "ML") AND "healthcare"     <-- Parentheses NOT supported!

The API uses the query_data for filtering, text should be simple keywords only.

Generate 5-6 simple keyword queries (space-separated, max 100 chars) in this format:
QUERY 1: "machine learning" healthcare
QUERY 2: "artificial intelligence" SME
QUERY 3: "digital health" Bulgaria
QUERY 4: AI "medical devices"
QUERY 5: healthcare innovation
QUERY 6: "clinical decision support"
"""

        return prompt

    def _parse_llm_queries(self, content: str) -> List[str]:
        """Parse queries from LLM response and enforce length limits."""
        queries = []
        MAX_QUERY_LENGTH = 100  # EU API limit

        # Look for patterns like "QUERY X:" or numbered lists
        lines = content.strip().split("\n")
        for line in lines:
            # Remove numbering and labels
            cleaned = re.sub(r"^(QUERY \d+:|\d+\.)\s*", "", line.strip())
            if cleaned and len(cleaned) > 10:
                # Truncate if too long
                if len(cleaned) > MAX_QUERY_LENGTH:
                    print(
                        f"[WARNING] Query too long ({len(cleaned)} chars), truncating to {MAX_QUERY_LENGTH}"
                    )
                    cleaned = (
                        cleaned[:MAX_QUERY_LENGTH].rsplit(" AND ", 1)[0]
                        if " AND " in cleaned
                        else cleaned[:MAX_QUERY_LENGTH]
                    )
                queries.append(cleaned)

        # If no queries found, try to extract quoted strings with AND/OR
        if not queries:
            pattern = r'"[^"]+"\s+AND\s+"[^"]+"'
            queries = re.findall(pattern, content)
            # Truncate if needed
            queries = [
                q[:MAX_QUERY_LENGTH] if len(q) > MAX_QUERY_LENGTH else q
                for q in queries
            ]

        return queries[:6] if queries else ["artificial intelligence AND SME"]

    def _generate_rule_based_queries(
        self, analysis: Dict, previous_feedback: str = None
    ) -> List[str]:
        """Generate queries using rules when LLM unavailable.
        Uses ALL company profile fields: name, type, country, employees, domains, description.
        """
        queries = []

        techs = analysis.get("technologies", [])
        apps = analysis.get("applications", [])
        keywords = analysis.get("keywords", [])
        name = analysis.get("name", "")
        company_type = analysis.get("type", "SME")
        country = analysis.get("country", "")
        employees = analysis.get("employees", 10)
        competencies = analysis.get("competencies", [])

        # Strategy 1: Primary Technology + Application (most specific)
        if techs and apps:
            queries.append(f'"{techs[0]}" AND "{apps[0]}"')

        # Strategy 2: Technology + Company Type + Country
        if techs and country:
            queries.append(f'"{techs[0]}" AND "{company_type}" AND "{country}"')
        elif techs:
            queries.append(f'"{techs[0]}" AND "{company_type}"')

        # Strategy 3: Two core technologies combined
        if len(techs) >= 2:
            queries.append(f'"{techs[0]}" AND "{techs[1]}"')

        # Strategy 4: Domain competency + Application
        if competencies and apps:
            comp_domain = competencies[0].get("domain", "")
            if comp_domain:
                queries.append(f'"{comp_domain}" AND "{apps[0]}"')

        # Strategy 5: Company size-appropriate keywords
        if employees < 50:
            # SME-specific queries
            if techs and apps:
                queries.append(f'"SME" AND "{techs[0]}" AND "{apps[0]}"')
            elif techs:
                queries.append(f'"SME" AND "{techs[0]}"')
        else:
            # Larger company queries
            if techs:
                queries.append(f'"enterprise" AND "{techs[0]}"')

        # Strategy 6: Extract industry from company name
        name_lower = name.lower()
        if any(word in name_lower for word in ["health", "medical", "bio"]):
            if techs:
                queries.append(f'"healthcare" AND "{techs[0]}"')
        elif any(word in name_lower for word in ["tech", "digital", "soft"]):
            if techs:
                queries.append(f'"digital" AND "{techs[0]}"')
        elif any(word in name_lower for word in ["green", "eco", "env"]):
            if techs:
                queries.append(f'"sustainability" AND "{techs[0]}"')

        # Strategy 7: Country-specific innovation
        if country and len(queries) < 5:
            if techs:
                queries.append(f'"innovation" AND "{country}" AND "{techs[0]}"')
            else:
                queries.append(f'"innovation" AND "{country}"')

        # Strategy 8: Top keywords combination
        if len(keywords) >= 2:
            queries.append(f'"{keywords[0]}" AND "{keywords[1]}"')

        # Apply feedback-based refinement
        if previous_feedback:
            queries = self._refine_queries(queries, previous_feedback, analysis)

        # Ensure minimum queries with fallback
        while len(queries) < 3:
            if techs and apps:
                queries.append(f'"{techs[0]}" AND "{apps[0]}"')
            elif techs:
                queries.append(f'"{techs[0]}" AND "innovation"')
            elif apps:
                queries.append(f'"{apps[0]}" AND "technology"')
            else:
                queries.append(f'"{company_type}" AND "innovation"')

        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for q in queries:
            if q not in seen:
                seen.add(q)
                unique_queries.append(q)

        return unique_queries[:6]

    def _refine_queries(
        self, queries: List[str], feedback: str, analysis: Dict
    ) -> List[str]:
        """Refine queries based on feedback."""
        refined = []
        feedback_lower = feedback.lower()

        # If too broad, add application context
        if "broad" in feedback_lower or "specific" in feedback_lower:
            apps = analysis.get("applications", [])
            for q in queries[:3]:
                if apps and not any(app in q.lower() for app in apps):
                    refined.append(f'{q} AND "{apps[0]}"')
                else:
                    refined.append(q)

        # If mentions adding keywords
        if "keyword" in feedback_lower:
            keywords = analysis.get("keywords", [])
            if len(keywords) >= 3:
                refined.append(
                    f'"{keywords[0]}" AND "{keywords[1]}" AND "{keywords[2]}"'
                )

        # If not refined, add a specific competency-based query
        if not refined:
            refined = queries.copy()
            if analysis.get("competencies") and analysis.get("applications"):
                comp = analysis["competencies"][0]
                app = analysis["applications"][0]
                specific = f'"{comp["domain"]}" AND "{app}" AND application'
                refined.insert(0, specific)

        return refined[:6]

    def create_plan(
        self, company_data: Dict[str, Any], previous_feedback: str = None
    ) -> Dict[str, Any]:
        """
        Create comprehensive execution plan with deep analysis.
        Maintains compatibility with existing scraper.
        """

        # Step 1: Deep analysis
        print(
            "   [ANALYZING] Extracting technologies, applications, and competencies..."
        )
        analysis = self.analyze_company_deep(company_data)

        # Step 2: Generate smart queries
        print(f"   [GENERATING] Creating targeted search queries...")
        if previous_feedback:
            print(f"   [REFINING] Applying feedback: {previous_feedback[:60]}...")

        queries = self.generate_queries_with_llm(analysis, previous_feedback)

        # Step 3: Build plan with same structure as before
        plan = {
            "company_name": analysis.get("name", "Unknown"),
            "company_type": analysis.get("type", "SME"),
            "search_queries": queries,
            "filter_config": STATIC_FILTER_CONFIG,  # Same config for scraper compatibility
            "target_programs": analysis.get("eu_programs", ["Horizon Europe"]),
            "estimated_calls": min(20, len(queries) * 3),
            "reasoning": self._build_reasoning(analysis, previous_feedback),
            "analysis": analysis,  # Extra info for debugging
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        }

        return plan

    def _build_reasoning(self, analysis: Dict, previous_feedback: str = None) -> str:
        """Build reasoning string."""
        techs = ", ".join(analysis.get("technologies", [])[:3])
        apps = ", ".join(analysis.get("applications", [])[:2])

        if previous_feedback:
            return f"Refined plan targeting: {techs} in {apps}. Addressed feedback."
        else:
            return f"Initial plan targeting: {techs} for {apps} applications. TRL {analysis.get('trl_level', 'unknown')}."


# Convenience function for backward compatibility
def create_smart_plan(
    company_data: Dict[str, Any], previous_feedback: str = None
) -> Dict[str, Any]:
    """Create plan using smart planner."""
    planner = SmartPlanner()
    return planner.create_plan(company_data, previous_feedback)
