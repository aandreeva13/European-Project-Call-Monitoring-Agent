'''python
# eu-call-finder/contracts/schemas.py
# Pydantic models (Input/Output structures)

from pydantic import BaseModel

class Call(BaseModel):
    id: str
    title: str
    description: str
    link: str
'''