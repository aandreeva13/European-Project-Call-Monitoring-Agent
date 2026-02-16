# EU Call Finder - Test Suite

Organized test files for the EU Call Finder workflow.

## Test Files

### 🎯 Main Workflow Tests (Use These)

| Test File | Description | What It Tests |
|-----------|-------------|---------------|
| `test_api_workflow.py` | **PRIMARY TEST** - API-only mode | Complete workflow using HTTP API (no browser needed) |
| `test_chrome_workflow.py` | Chrome browser test | Complete workflow with Chrome WebDriver |
| `test_safety_planner.py` | Safety + Planning only | Validates Safety Guard and Planner Agent |

### 🔧 Component Tests

| Test File | Description |
|-----------|-------------|
| `test_input_validator.py` | Input validation logic |
| `test_safety_guard.py` | Security checks (prompt injection, XSS, etc.) |
| `test_planner_llm.py` | LLM-based planning |
| `test_analysis.py` | Analysis modules (scoring, eligibility) |
| `test_analysis_modules.py` | Analysis module connections |
| `test_llm_critic.py` | LLM qualitative analysis |
| `test_planner_vs_retrieval.py` | Planner and retrieval integration |

## How to Run Tests

### Quick Test (Recommended)
```bash
cd eu-call-finder
python tests/test_api_workflow.py
```

This runs the complete workflow using the EU Funding Portal API - **no browser needed!**

### Component Tests
```bash
# Test individual components
python tests/test_safety_guard.py
python tests/test_planner_llm.py
python tests/test_analysis.py
```

## Test Results

Tests generate reports in this folder:
- `test_full_report.json` - Final workflow results

## Notes

- **API mode** is the recommended way (fast, reliable, official EU API)
- **Chrome mode** requires working ChromeDriver (may have version issues)
- All tests use the actual implementation code (not mocks)
