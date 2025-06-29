from datetime import datetime

from pydantic import BaseModel, Field


class PracticeRecordSchema(BaseModel):
    id: str = Field(..., alias="_id")
    sign_id: str
    accuracy: float
    practice_image_url: str
    created_at: datetime

    class Config:
        allow_population_by_field_name = True
        orm_mode = True
