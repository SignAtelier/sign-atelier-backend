from datetime import datetime
from typing import Optional

from beanie import Link

from app.models.base import BaseDocument
from app.models.user import User


class Sign(BaseDocument):
    user: Link[User]
    name: str
    file_name: str
    outline_file_name: str
    is_deleted: bool = False
    deleted_at: Optional[datetime] = None

    class Settings:
        name = "signs"
