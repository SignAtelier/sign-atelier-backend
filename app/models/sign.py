from datetime import datetime

from beanie import Document
from bson import ObjectId
from pydantic import Field


class Sign(Document):
    user_id: ObjectId
    sign_image_url: str
    created_at: datetime = Field(default_factory=datetime.now(datetime.UTC))
    updated_at: datetime = Field(default_factory=datetime.now(datetime.UTC))
    is_deleted: bool = False

    class Settings:
        name = "signs"
