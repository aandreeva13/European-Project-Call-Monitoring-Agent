'''python
# eu-call-finder/main.py
# FastAPI app entry point

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "eu-call-finder is running!"}
'''