import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from starlette.config import Config

from app.config.constants import CODE, MESSAGE, CleanupInterval
from app.db.crud.sign import get_deleted_signs
from app.db.session import client, db, init_db
from app.exception.custom_exception import AppException
from app.utils.cleanup import hard_delete_process


config = Config(".env")


@asynccontextmanager
async def connect_db(application):
    await init_db()

    ping_response = await db.command("ping")

    if int(ping_response["ok"]) != 1:
        raise AppException(
            status=500,
            code=CODE.ERROR.DB_CONNECTION_FAILED,
            message=MESSAGE.ERROR.DB_CONNECTION_FAILED,
        )

    application.mongodb_client = client
    application.database = db

    try:
        yield
    finally:
        client.close()


async def _cleanup_loop():
    while True:
        deleted_signs = await get_deleted_signs()
        now = datetime.now(timezone.utc)

        for sign in deleted_signs:
            sign.deleted_at = sign.deleted_at.replace(tzinfo=timezone.utc)
            if sign.deleted_at < now:
                await hard_delete_process(sign)

        await asyncio.sleep(CleanupInterval.SECONDS)


@asynccontextmanager
async def cleanup_garbage():
    task = asyncio.create_task(_cleanup_loop())

    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
