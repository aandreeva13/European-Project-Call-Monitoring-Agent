# Shift log / Handover notes

Project: **European-Project-Call-Monitoring-Agent** (EU Call Finder)

Date: **2026-02-18**

## How to use this file

- Add a new section per person per day (keep it chronological).
- Each section should include:
  - **What was fixed/changed** (with file links)
  - **What needs to be fixed next** (actionable)
  - **Notes / context** (why)

## Today’s entries

### Andi

#### What was fixed/changed

- Added UI-aligned company fixtures: [`eu-call-finder/tests/fixtures/company_examples.json`](eu-call-finder/tests/fixtures/company_examples.json:1)
- Added “known-good” search term examples + ready-to-post bodies (note: request keywords currently not used by workflow):
  - [`eu-call-finder/tests/fixtures/working_search_examples.json`](eu-call-finder/tests/fixtures/working_search_examples.json:1)
  - [`eu-call-finder/tests/fixtures/working_request_robotics.json`](eu-call-finder/tests/fixtures/working_request_robotics.json:1)
  - [`eu-call-finder/tests/fixtures/working_request_cyber.json`](eu-call-finder/tests/fixtures/working_request_cyber.json:1)
  - [`eu-call-finder/tests/fixtures/working_request_energy.json`](eu-call-finder/tests/fixtures/working_request_energy.json:1)
- Adjusted scoring to avoid hard-failing when LLM insights are missing: [`score_call()`](eu-call-finder/5_analysis/scorer.py:1)

#### What needs to be fixed next (updated from energy.json test output)

##### 1) Planner quality for energy companies (Solaris Microgrids GmbH)

Observed in `/api/search/stream` run:
- Planner extracted **empty** `Technologies Detected`, `Applications`, `Focus Areas` despite energy/microgrids/battery/inverter text in the input.
- Generated generic queries: `"innovation" AND "Germany"`, `"energy" AND "develop"`, `"SME" AND "innovation"`.

Likely root causes:
- [`SmartPlanner.analyze_company_deep()`](eu-call-finder/3_planning/smart_planner.py:35) has limited patterns; energy app keywords omit important terms like `microgrid`, `battery storage`, `BESS`, `inverter`, `EMS`.

Impact:
- Retrieval becomes noisy and returns generic SME-innovation topics rather than energy/microgrid-specific calls.

Fix:
- Improve extraction + query generation in [`create_smart_plan()`](eu-call-finder/3_planning/smart_planner.py:1) to reliably emit energy-domain terms.
- Add a deterministic “energy/microgrid keyword pack” fallback when the planner extraction is empty.
  - Example terms: `microgrid`, `energy management system`, `EMS`, `battery energy storage`, `BESS`, `grid-forming inverter`, `inverter control`, `demand response`, `industrial sites`, `power electronics`.

##### 2) Retrieval should capture richer call content for analysis

Observed in UI/screens:
- Call details show **“No detailed description available.”**

Impact:
- Rule-based scoring and LLM critique have minimal signal (`content.description` empty), causing “weak match” boilerplate and mid/low totals.

Fix:
- Ensure scraper populates `content.description`, `keywords`, and (if possible) `required_domains`.
- If EU Search API only returns summary fields, follow the call URL and scrape the detail page.
  - Candidate owner: [`ScraperManager`](eu-call-finder/4_retrieval/scraper_manager.py:1)

##### 3) Analysis/Scoring: make “PASS” and scores honest under missing data

Observed:
- Many eligibility checks treat missing constraints as pass (e.g. `eligible_countries` empty => pass).

Impact:
- “Eligibility: PASS” can mean “unknown”, and scores ~5–6 can be artifacts of missing text rather than real mismatch.

Fix:
- Add an explicit `unknown`/`insufficient_data` flag in eligibility output from [`apply_eligibility_filters()`](eu-call-finder/5_analysis/eligibility.py:1).
- Add a data-quality/confidence penalty or badge in scoring/reporting when description/domains/keywords are missing.
  - Scoring entrypoint: [`score_call()`](eu-call-finder/5_analysis/scorer.py:4)
  - Confidence helper already exists: [`evaluate_confidence()`](eu-call-finder/5_analysis/reflection.py:186)

##### 4) Keep existing high-impact fix: planner → retrieval query incompatibility

- Fix planner → retrieval search terms incompatibility (planner emits quoted Boolean strings; EU Search API `text` expects plain terms).
  - See: [`planner_node()`](eu-call-finder/2_orchestration/master_agent.py:284) → [`_api_search_topics()`](eu-call-finder/4_retrieval/scraper_manager.py:119)
- Optionally widen planner filter config to include `type "2"` like scraper default.
  - See: [`STATIC_FILTER_CONFIG`](eu-call-finder/3_planning/smart_planner.py:13) vs [`default_search_query()`](eu-call-finder/4_retrieval/scraper_manager.py:178)
- Decide whether API request `keywords` should override/merge with planner queries (currently ignored by workflow): [`search_calls_stream()`](eu-call-finder/api/routes.py:89)

##### 5) Duplicate workflow runs / duplicated logs in `/api/search/stream`

Observed:
- Same `/api/search/stream` request appears to trigger two workflow executions (duplicate “STARTING… STEP 1..5” blocks) and duplicated progress markers.

Likely root causes:
- Frontend double-invocation (React 18 dev StrictMode, event handler wired twice, or retry logic around SSE/fetch).
- Backend log amplification: [`patched_print()`](eu-call-finder/api/routes.py:154) calls `print("[PROGRESS] ...")` *inside* the patched `print`, which can cascade/duplicate noisy progress lines.

Fix:
- Frontend: ensure only one POST is issued per user action; audit caller in [`apiService.ts`](eu-call-finder/frontend/ui/services/apiService.ts:1) and the triggering component (likely Step 3).
- Backend: change progress emission to call `original_print(...)` for progress lines (or guard with a flag) so the patched handler doesn’t re-enter itself.

#### Notes / context

- Root cause of 0 topics is documented under “Why the API workflow returns 0 topics” below.
- Energy.json test demonstrated the second-order issue: even when retrieval returns topics, missing call detail text makes analysis and scores unreliable.

### _YourNameHere_

#### What was fixed/changed

-

#### What needs to be fixed next

-

#### Notes / context

-

---

## Summary of findings

### Why the API workflow returns 0 topics

The end-to-end workflow completes successfully, but retrieval returns **0 topics**, so analysis runs on an empty list and the reporter generates a fallback report.

Root cause is the **planner → retrieval handoff**:

- Planner emits Boolean-style search strings like `"robotics" AND "transport"`.
- Retrieval passes those strings into the EU Search API `text` parameter.
- The EU Search API `text` behaves like a **plain text search**, not a Boolean query language.
  - Quoted + `AND`-heavy strings often yield **0 hits**.

See:
- Planner node uses `plan["search_queries"]` as `search_terms`: [`planner_node()`](eu-call-finder/2_orchestration/master_agent.py:284)
- Retrieval passes `search_terms` directly to EU API: [`_api_search_topics()`](eu-call-finder/4_retrieval/scraper_manager.py:119)

Additional factor: planner’s filter config is **more restrictive** than scraper default:
- Planner filter: [`STATIC_FILTER_CONFIG`](eu-call-finder/3_planning/smart_planner.py:13) uses `type: ["1","8"]`
- Scraper default: [`default_search_query()`](eu-call-finder/4_retrieval/scraper_manager.py:178) uses `type: ["1","2","8"]`

If relevant indexed items are `type "2"` for certain queries, planner filter will exclude them.

## What was changed in this shift

### 1) Added realistic UI-aligned company fixtures

Created JSON fixtures matching the frontend “Organization Details” + “Domains of Expertise” fields.

- Added: [`eu-call-finder/tests/fixtures/company_examples.json`](eu-call-finder/tests/fixtures/company_examples.json:1)
  - 12 examples across robotics, energy, health, circular materials, cybersecurity, agritech, mobility, biosensors, photonics, water, space, fintech.
  - Schema used in these fixtures corresponds to the UI labels:
    - `companyName`, `organizationType`, `country`, `city`, `numberOfEmployees`, `coreActivitiesAndMission`
    - `domainsOfExpertise[]: { domainName, expertiseLevel, subDomains[] }`

### 2) Added “known-good” retrieval search term examples + request bodies

Goal: provide examples that are likely to produce topics **when directly used as `search_terms`** in the EU Search API.

- Added: [`eu-call-finder/tests/fixtures/working_search_examples.json`](eu-call-finder/tests/fixtures/working_search_examples.json:1)
- Added ready-to-post bodies:
  - [`eu-call-finder/tests/fixtures/working_request_robotics.json`](eu-call-finder/tests/fixtures/working_request_robotics.json:1)
  - [`eu-call-finder/tests/fixtures/working_request_cyber.json`](eu-call-finder/tests/fixtures/working_request_cyber.json:1)
  - [`eu-call-finder/tests/fixtures/working_request_energy.json`](eu-call-finder/tests/fixtures/working_request_energy.json:1)

Important: these request bodies do **not** currently influence retrieval because `keywords` is stored but not used by the planner/retrieval path.

### 3) Verified EU Search API can return topics (retrieval works with plain terms)

Ran a direct call to the retrieval helper to confirm the API returns topics with broad, plain keywords:

- Terms like `Horizon Europe`, `HORIZON-CL`, `HORIZON-EIC`, `innovation` returned **70 topics**.
- Verification was performed against [`_api_search_topics()`](eu-call-finder/4_retrieval/scraper_manager.py:119).

## What each area needs next (actionable)

### A) Planner fixes (most important)

Problem: Planner generates strings that the EU Search API `text` parameter doesn’t interpret as intended.

Options:

1. **Emit plain search terms (recommended quick fix)**
   - Replace Boolean/quoted outputs with plain, short terms.
   - Examples: `HORIZON-CL4`, `HORIZON-CL3`, `EIC Accelerator`, `Digital Europe`, `robotics`, `cybersecurity`.
   - Implement in: [`create_smart_plan()`](eu-call-finder/3_planning/smart_planner.py:1) (where queries are generated).

2. **Sanitize queries before retrieval**
   - In retrieval node (or before calling `_api_search_topics`), transform:
     - remove quotes
     - replace ` AND ` with space
     - drop country/type tokens that harm recall
   - Candidate location: [`retrieval_node()`](eu-call-finder/2_orchestration/master_agent.py:390)

3. **Widen the planner filter config**
   - Align planner filter with scraper default by including `type "2"`:
     - change [`STATIC_FILTER_CONFIG`](eu-call-finder/3_planning/smart_planner.py:13) to `type: ["1","2","8"]`.

### B) API/Workflow: actually use request keywords

Current behavior:
- API accepts `keywords` in request body and stores them in `company_input`.
- Planner ignores them and overwrites `search_terms` with its own generated `search_queries`.

Fix options:

1. **Let request keywords override planner queries** (simple and user-controlled)
   - If `company_input["keywords"]` is non-empty, set `state["search_terms"] = keywords` and skip planner query generation.
   - Candidate location: [`planner_node()`](eu-call-finder/2_orchestration/master_agent.py:284)

2. **Merge keywords into planner output**
   - `search_terms = unique(plan_queries + request_keywords)`.

### C) Analysis logic

Scoring logic was adjusted to **avoid hard failure when LLM insights are missing**.

- Updated: [`score_call()`](eu-call-finder/5_analysis/scorer.py:1)
  - Previous behavior: raised `ValueError` if `llm_insights` missing or `analysis_method != "llm"`.
  - New behavior: if LLM insights are present and `analysis_method == "llm"`, use LLM-enhanced scoring; otherwise **fall back to deterministic rule-based scoring** for domain/keyword/strategic criteria.
  - Keeps workflow usable in offline / keyless environments.

The analysis “0 results” issue is still primarily a consequence of empty retrieval results:
- Analyzer correctly warns and triggers planner refinement.
- After 3 attempts, workflow continues with empty results by design.

## How to reproduce the issue quickly

1. Use the API endpoint and observe planner emitting Boolean/quoted search strings:
   - Endpoint: [`/api/search/stream`](eu-call-finder/api/routes.py:89)

2. Observe retrieval calling EU Search API with those terms:
   - Retrieval helper: [`_api_search_topics()`](eu-call-finder/4_retrieval/scraper_manager.py:119)

3. Observe `Retrieved 0 topics` and fallback report.

## Notes / conventions

- The numbered folder modules are loaded via importlib in the master agent: [`_load_module()`](eu-call-finder/2_orchestration/master_agent.py:36)
- Retrieval uses EU search API endpoint `https://api.tech.ec.europa.eu/search-api/prod/rest/search` in [`_api_search_topics()`](eu-call-finder/4_retrieval/scraper_manager.py:119)
