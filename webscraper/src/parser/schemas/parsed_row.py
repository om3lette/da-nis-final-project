from pydantic import BaseModel

class ParsedRowSchema(BaseModel):
    most_popular: str
    field_name: str
    pct: float
