from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config.constants import CODE, MESSAGE
from app.db.session import client, db, init_db
from app.exception.custom_exception import AppException

load_dotenv(override=True)


@asynccontextmanager
async def db_lifespan(application: FastAPI):
    try:
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

        yield

    finally:
        client.close()


app = FastAPI(lifespan=db_lifespan)


@app.get("/")
def read_root():
    return


@app.exception_handler(AppException)
async def custom_exception_handler(_: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status,
        content={
            "status": exc.status,
            "code": exc.code,
            "message": exc.message,
        },
    )
