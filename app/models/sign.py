from beanie import Link

from app.models.base import BaseDocument
from app.models.user import User


class Sign(BaseDocument):
    user: Link[User]
    sign_image_url: str
    is_deleted: bool = False

    class Settings:
        name = "signs"
