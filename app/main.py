from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.core.constants import MESSAGE
from app.db.session import client, db
from app.exception.custom_exception import AppException

load_dotenv(override=True)


async def db_lifespan(application: FastAPI):
    application.mongodb_client = client
    application.database = db
    ping_response = await application.database.command("ping")
    if int(ping_response["ok"]) != 1:
        raise AppException(status=500, message=MESSAGE.ERROR.DB_CONNECTION_FAILED)

    yield

    app.mongodb_client.close()


app = FastAPI(lifespan=db_lifespan)


@app.get("/")
def read_root():
    raise AppException(status=400, message=MESSAGE.ERROR.NOT_FOUND)


@app.exception_handler(AppException)
async def custom_exception_handler(_: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status,
        content={"status": exc.status, "message": exc.message},
    )
