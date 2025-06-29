from datetime import datetime
from typing import Optional

from beanie import Document
from pydantic import Field


class User(Document):
    google_id: str
    profile_image: Optional[str]
    created_at: datetime = Field(default_factory=datetime.now(datetime.UTC))
    updated_at: datetime = Field(default_factory=datetime.now(datetime.UTC))
    deleted: bool = False

    class Settings:
        name = "users"
