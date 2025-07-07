from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exception.custom_exception import AppException

load_dotenv(override=True)


app = FastAPI()


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
