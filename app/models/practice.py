from beanie import Link

from app.models.base import BaseDocument
from app.models.sign import Sign


class PracticeRecord(BaseDocument):
    sign: Link[Sign]
    file_name: str

    class Settings:
        name = "practice_records"
