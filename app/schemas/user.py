from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserSchema(BaseModel):
    id: str = Field(..., alias="_id")
    google_id: str
    profile_image: Optional[str]
    created_at: datetime
    updated_at: datetime
    deleted: bool

    class Config:
        allow_population_by_field_name = True
        orm_mode = True
