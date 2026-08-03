from pydantic import BaseModel

class PolicyQuery(BaseModel):
    question: str
    
    # Can add other fields later if needed, like:
    # department: str 
    # urgency: int