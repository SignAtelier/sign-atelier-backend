from fastapi import APIRouter, Body, Cookie
from fastapi.responses import JSONResponse, Response

from app.config.constants import CODE, COOKIE, MESSAGE
from app.exception.custom_exception import AppException
from app.services.auth_service import (
    create_google_refresh_token,
    reissue_access_token,
    verify_google_credential,
)

router = APIRouter()


@router.post("/google")
async def google_sdk_login(credential: str = Body(..., embed=True)):
    userinfo = await verify_google_credential(credential)
    refresh_token = await create_google_refresh_token(userinfo)
    access_token = await reissue_access_token(refresh_token)
    response = JSONResponse({"accessToken": access_token})

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=COOKIE.MaxAge.REFRESH,
    )

    return response


@router.post("/refresh")
async def refresh_access_token(
    refresh_token: str = Cookie(None),
):
    if not refresh_token:
        raise AppException(
            status=401,
            code=CODE.ERROR.MISSING_REFRESH_TOKEN,
            message=MESSAGE.ERROR.MISSING_REFRESH_TOKEN,
        )

    access_token = await reissue_access_token(refresh_token)

    return {"accessToken": access_token}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("refresh_token")
