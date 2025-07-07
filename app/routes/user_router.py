from fastapi import APIRouter, Depends

from app.depends.auth_deps import get_current_user

router = APIRouter()


@router.get("/me")
async def get_user(user=Depends(get_current_user)):
    return user
