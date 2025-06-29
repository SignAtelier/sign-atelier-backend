from datetime import datetime

from pydantic import BaseModel, Field


class SignSchema(BaseModel):
    id: str = Field(..., alias="_id")
    user_id: str
    sign_image_url: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        allow_population_by_field_name = True
        orm_mode = True
