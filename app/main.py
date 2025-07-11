from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware

from app.config.constants import CLIENT, CODE, MESSAGE
from app.db.session import client, db, init_db
from app.exception.custom_exception import AppException
from app.routes import (
    auth_router,
    practice_router,
    s3_router,
    sign_router,
    user_router,
)


load_dotenv(override=True)

config = Config(".env")


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

app.add_middleware(SessionMiddleware, secret_key=config("SECRET_KEY"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CLIENT.URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return RedirectResponse(CLIENT.URL)


app.include_router(auth_router.router, prefix="/api/auth")
app.include_router(user_router.router, prefix="/api/users")
app.include_router(sign_router.router, prefix="/api/signs")
app.include_router(practice_router.router, prefix="/api/practices")
app.include_router(s3_router.router, prefix="/api/s3")


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
