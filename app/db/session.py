import os

from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(os.environ["MONGO_URI"])
db = client[os.environ["MONGO_DB"]]
