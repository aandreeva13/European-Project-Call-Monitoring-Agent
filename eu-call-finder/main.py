"""
eu-call-finder/main.py
FastAPI app entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router

app = FastAPI(
    title="EU Call Finder API",
    description="API for finding and analyzing EU funding calls",
    version="1.0.0",
)

# Add CORS middleware to allow frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "EU Call Finder API is running!", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
