from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from starlette.config import Config

from app.models.practice import PracticeRecord
from app.models.sign import Sign
from app.models.user import User

config = Config(".env")

client = AsyncIOMotorClient(config("MONGO_URI"))
db = client[config("MONGO_DB")]


async def init_db():
    await init_beanie(
        database=db, document_models=[User, PracticeRecord, Sign]
    )
