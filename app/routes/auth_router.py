from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.config.auth import oauth
from app.config.constants import TOKEN
from app.services.auth_service import fetch_google_userinfo, handle_google_auth

router = APIRouter()


@router.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth_google")

    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google", name="auth_google")
async def auth(request: Request):
    userinfo = await fetch_google_userinfo(request)
    access_token = await handle_google_auth(userinfo, "google")

    redirect_uri = "http://localhost:5173"

    response = RedirectResponse(url=redirect_uri)
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=TOKEN.EXPIRE.ACCESS,
    )

    return response
