from fastapi import APIRouter, Cookie, Request
from fastapi.responses import RedirectResponse, Response

from app.config.auth import oauth
from app.config.constants import CODE, COOKIE, MESSAGE
from app.exception.custom_exception import AppException
from app.services.auth_service import (
    fetch_google_userinfo,
    handle_google_auth,
    reissue_access_token,
)

router = APIRouter()


@router.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth_google")

    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google", name="auth_google")
async def auth(request: Request):
    userinfo = await fetch_google_userinfo(request)
    tokens = await handle_google_auth(userinfo, "google")

    redirect_uri = "http://localhost:5173"

    response = RedirectResponse(url=redirect_uri)
    response.set_cookie(
        key="access_token",
        value=tokens["access_token"],
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=COOKIE.MaxAge.ACCESS,
    )
    response.set_cookie(
        key="refresh_token",
        value=tokens["refresh_token"],
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
    response = Response()
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=COOKIE.MaxAge.ACCESS,
    )

    return response
