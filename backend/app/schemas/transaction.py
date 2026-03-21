from pydantic import BaseModel, field_validator, Field
from datetime import datetime
from typing import Optional

class CreateTransaction(BaseModel):
    date: Optional[datetime] = Field(default=None)
    amount: float
    category: Optional[str] = Field(default="UNCATEGORIZED")
    subscription_id: Optional[int] = Field(default=None)
    goal_id: Optional[int] = Field(default=None)
    description: str

    @field_validator("amount")
    @classmethod
    def amount_validator(cls, v):
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        return v

    @field_validator("subscription_id", "goal_id", mode="before")
    @classmethod
    def convert_zero_to_none(cls, v):
        # Convert 0 to None since there's no subscription/goal with ID 0
        if v == 0 or v == "0":
            return None
        return v

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if v is None or v == "":
            return datetime.now()
        if isinstance(v, datetime):
            # Remove timezone info to match TIMESTAMP WITHOUT TIME ZONE
            return v.replace(tzinfo=None) if v.tzinfo else v
        # If it's a string, parse it and remove timezone
        if isinstance(v, str):
            try:
                # Try ISO format first (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS)
                parsed = datetime.fromisoformat(v.replace('Z', '+00:00'))
                return parsed.replace(tzinfo=None) if parsed.tzinfo else parsed
            except ValueError:
                # If ISO format fails, try other formats
                try:
                    return datetime.strptime(v, "%Y-%m-%d").replace(tzinfo=None)
                except ValueError:
                    return datetime.now()
        return v

class CategorizeRequest(BaseModel):
    category: str

class ViewTransaction(BaseModel):
    id: int
    date: datetime
    amount: float
    category: str
    subscription_id: int | None = None
    goal_id: int | None = None
    description: str

    class config:
        from_attribute = False


