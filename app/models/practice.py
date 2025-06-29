from beanie import Link

from app.models.base import BaseDocument
from app.models.sign import Sign


class PracticeRecord(BaseDocument):
    sign_id: Link[Sign]
    practice_image_url: str

    class Settings:
        name = "practice_records"
