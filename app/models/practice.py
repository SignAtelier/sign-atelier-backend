from datetime import datetime

from beanie import Document
from bson import ObjectId
from pydantic import Field


class PracticeRecord(Document):
    sign_id: ObjectId
    accuracy: float
    practice_image_url: str
    created_at: datetime = Field(default_factory=datetime.now(datetime.UTC))

    class Settings:
        name = "practice_records"
