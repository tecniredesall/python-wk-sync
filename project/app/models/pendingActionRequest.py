from pydantic import BaseModel
from typing import Dict


class PendingAction(BaseModel):
    action: str
    request_payload: Dict
    
    class Config:
        schema_extra = {
            "example": {
                "action": "random-sorting",
                "request_payload": {
                    "items": ["a", "b", "c", "d", "e"]
                }
            }
        }
    