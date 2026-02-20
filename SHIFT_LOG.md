# Shift Log / Handover Notes

Project: **European-Project-Call-Monitoring-Agent** (EU Call Finder)  
Date: **2026-02-19**

---

## Andi

### ✅ Changes / Findings (2026-02-19)
- UI: centered the header History icon by making the button a fixed-size flex container and removing icon line-height drift in [`Layout.tsx`](eu-call-finder/frontend/ui/components/Layout.tsx:40).
- Debug: verified scoring inputs for the latest run; `company_profile.keywords` is missing/`None` in [`final_report_20260219_154403.json`](eu-call-finder/final_report_20260219_154403.json:1), which explains depressed `keyword_match` from [`_score_keyword_match()`](eu-call-finder/5_analysis/scorer.py:250).

---

# Shift Log / Handover Notes

Project: **European-Project-Call-Monitoring-Agent** (EU Call Finder)  
Date: **2026-02-18**

---

## Status Overview

| Component | Status | Notes |
|-----------|--------|-------|
| History Feature | ✅ Working | Caches and displays previous results |
| Scoring Logic | ✅ Fixed | Match percentages now accurate |
| Planner | ⚠️ Needs Fix | Boolean queries incompatible with EU API |
| Retrieval | ⚠️ Partial | Works with plain terms but not with planner output |
| Analysis | ✅ Working | LLM + rule-based fallback functional |

---

## ✅ What Was Fixed

### 1. History Feature - Cache and Display Search Results
**Problem:** Clicking history items re-ran the entire workflow instead of showing cached results.  
**Solution:** Extended session storage to persist complete search results.

**Files Modified:**
- [`App.tsx`](eu-call-finder/frontend/ui/App.tsx:1) - Added `cachedResult` state, session ID tracking
- [`Layout.tsx`](eu-call-finder/frontend/ui/components/Layout.tsx:1) - Updated history click handler
- [`Step3Results.tsx`](eu-call-finder/frontend/ui/components/Step3Results.tsx:1) - Added cached result support, skips workflow if results exist

**How it works:**
- Each session now stores the full `SearchResult` object in localStorage
- Sessions matched by unique ID (not company name)
- Clicking any history item displays results instantly without re-running the 5-agent workflow
- Works for both successful searches AND "no matches" results

---

### 2. Analysis Scoring Logic (Commit: `c5d81fedc1da971f4d63779665e1acfe5305edcf`)
**Problem:** Match percentages and total scores were not calculating correctly.  
**Solution:** Fixed weighted scoring calculation and data quality penalty application.

**Changes:**
- Corrected weighted scoring across all 6 criteria (Domain 30%, Keywords 15%, Eligibility 20%, Budget 15%, Strategic 10%, Deadline 10%)
- Fixed score normalization from 1-10 scale to percentage display
- Resolved timing of data quality penalty application
- **Result:** Match percentages now accurately reflect company-call compatibility

**Previous Fix (LLM Fallback):**
- Scoring now falls back to rule-based when LLM unavailable
- Prevents `ValueError` crashes in offline/keyless environments

---

### 3. Test Fixtures and Examples
**Added:**
- [`company_examples.json`](eu-call-finder/tests/fixtures/company_examples.json:1) - 12 realistic company profiles across domains
- [`working_search_examples.json`](eu-call-finder/tests/fixtures/working_search_examples.json:1) - Known-good search terms
- [`working_request_robotics.json`](eu-call-finder/tests/fixtures/working_request_robotics.json:1) - Ready-to-post request body
- [`working_request_cyber.json`](eu-call-finder/tests/fixtures/working_request_cyber.json:1) - Ready-to-post request body
- [`working_request_energy.json`](eu-call-finder/tests/fixtures/working_request_energy.json:1) - Ready-to-post request body

**Verified:**
- EU Search API works with plain terms (e.g., `Horizon Europe`, `innovation` returns 70 topics)
- Retrieval module functional when given correct input

---

## ⚠️ What Needs Fixing

### 1. Planner → Retrieval Query Compatibility (CRITICAL)
**Problem:**  
Planner emits Boolean-style queries: `"robotics" AND "transport"`  
EU Search API `text` parameter treats these as plain text → **0 results returned**

**Root Cause:**
- Location: [`planner_node()`](eu-call-finder/2_orchestration/master_agent.py:284) → [`_api_search_topics()`](eu-call-finder/4_retrieval/scraper_manager.py:119)
- Planner generates: `"innovation" AND "Germany"`, `"energy" AND "develop"`
- EU API expects: `innovation Germany`, `energy develop`

**Solutions (pick one):**

| Option | Approach | Effort | Location |
|--------|----------|--------|----------|
| A | Emit plain terms from planner | Low | [`create_smart_plan()`](eu-call-finder/3_planning/smart_planner.py:1) |
| B | Sanitize queries before API call | Medium | [`retrieval_node()`](eu-call-finder/2_orchestration/master_agent.py:390) |
| C | Widen filter config (include type "2") | Low | [`STATIC_FILTER_CONFIG`](eu-call-finder/3_planning/smart_planner.py:13) |

**Recommended:** Option A - Change planner to output plain terms like: `HORIZON-CL4`, `robotics`, `cybersecurity`, `EIC Accelerator`

---

### 2. Planner Quality for Domain-Specific Companies
**Problem:**  
Planner extracts empty `Technologies`, `Applications`, `Focus Areas` for energy/microgrid companies.

**Example:** Solaris Microgrids GmbH input produces:
- Detected technologies: `[]` (empty)
- Queries: `"innovation" AND "Germany"`, `"SME" AND "innovation"` (too generic)

**Fix:**
- Add energy-domain keyword patterns: `microgrid`, `BESS`, `battery storage`, `inverter`, `EMS`, `grid-forming`
- Location: [`SmartPlanner.analyze_company_deep()`](eu-call-finder/3_planning/smart_planner.py:35)

---

### 3. API/Workflow: Use Request Keywords
**Problem:**  
API accepts `keywords` in request body but planner ignores them.

**Current Flow:**
```
Request.keywords → stored in company_input → planner overwrites with generated queries
```

**Fix Options:**
1. **Override mode:** If `company_input["keywords"]` provided, skip planner generation
2. **Merge mode:** Combine planner queries + request keywords: `unique(plan_queries + request_keywords)`

**Location:** [`planner_node()`](eu-call-finder/2_orchestration/master_agent.py:284)

---

### 4. Retrieval: Capture Richer Call Content
**Problem:**  
Call details show "No detailed description available" - insufficient data for analysis.

**Impact:**
- Scoring has minimal signal → mid/low totals
- LLM critique produces "weak match" boilerplate

**Fix:**
- Scraper should populate `content.description`, `keywords`, `required_domains`
- If EU Search API only returns summaries, follow call URL and scrape detail page
- Location: [`ScraperManager`](eu-call-finder/4_retrieval/scraper_manager.py:1)

---

### 5. Eligibility: Handle Missing Data
**Problem:**  
Missing eligibility fields treated as "pass" (e.g., empty `eligible_countries` → passes).

**Impact:**
- "Eligibility: PASS" can mean "unknown"
- Scores 5-6 may be artifacts of missing data, not real mismatches

**Fix:**
- Add `unknown`/`insufficient_data` flag in [`apply_eligibility_filters()`](eu-call-finder/5_analysis/eligibility.py:1)
- Add data-quality penalty/badge in reporting
- Helper exists: [`evaluate_confidence()`](eu-call-finder/5_analysis/reflection.py:186)

---

### 6. Duplicate Workflow Runs
**Problem:**  
Same `/api/search/stream` request triggers two workflow executions.

**Symptoms:**
- Duplicate "STARTING... STEP 1..5" logs
- Duplicated progress markers

**Likely Causes:**
- Frontend double-invocation (React StrictMode, event handler wired twice)
- Backend: [`patched_print()`](eu-call-finder/api/routes.py:154) calls progress inside patched print → cascades

**Fix:**
- Frontend: Audit [`apiService.ts`](eu-call-finder/frontend/ui/services/apiService.ts:1) and Step 3 component
- Backend: Change progress emission to use `original_print()` or add guard flag

---

## Quick Reference

### File Locations

| Component | Key Files |
|-----------|-----------|
| Frontend UI | [`App.tsx`](eu-call-finder/frontend/ui/App.tsx:1), [`Step3Results.tsx`](eu-call-finder/frontend/ui/components/Step3Results.tsx:1), [`Layout.tsx`](eu-call-finder/frontend/ui/components/Layout.tsx:1) |
| Master Agent | [`master_agent.py`](eu-call-finder/2_orchestration/master_agent.py:1) |
| Planner | [`smart_planner.py`](eu-call-finder/3_planning/smart_planner.py:1) |
| Retrieval | [`scraper_manager.py`](eu-call-finder/4_retrieval/scraper_manager.py:1) |
| Analysis | [`scorer.py`](eu-call-finder/5_analysis/scorer.py:1), [`eligibility.py`](eu-call-finder/5_analysis/eligibility.py:1) |
| API Routes | [`routes.py`](eu-call-finder/api/routes.py:1) |

### EU Search API

- **Endpoint:** `https://api.tech.ec.europa.eu/search-api/prod/rest/search`
- **Parameter:** `text` (plain text, NOT Boolean query language)
- **Working terms:** `Horizon Europe`, `HORIZON-CL`, `innovation`
- **Broken terms:** `"robotics" AND "transport"` (quotes and AND cause 0 results)

### History Storage

- **Key:** `eurofundfinder:sessions:v1`
- **Max entries:** 20
- **Structure:** `{ id, createdAt, company, result? }`
- **Session matching:** By unique ID (prevents collisions between companies with same name)
