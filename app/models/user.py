from app.models.base import BaseDocument


class User(BaseDocument):
    social_id: str
    provider: str
    profile: str
    isDeleted: bool = False

    class Settings:
        name = "users"
