'''python
# eu-call-finder/api/routes.py
# Endpoints triggering the Orchestrator

from fastapi import APIRouter

router = APIRouter()

@router.get("/search")
async def search_calls(query: str):
    # Trigger the orchestrator with the search query
    return {"message": f"Searching for calls with query: {query}"}
'''