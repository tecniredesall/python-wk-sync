from pydantic import BaseModel


# Pydantic BaseModel
# TestTask class model for request body
class TestTask(BaseModel):
    type: int