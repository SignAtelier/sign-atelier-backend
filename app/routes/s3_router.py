from typing import List

from fastapi import APIRouter, Depends

from app.depends.auth_deps import get_current_user
from app.services.s3_service import generate_urls


router = APIRouter()


@router.post("/presigned")
async def get_presigned_url(keys: List[str], _=Depends(get_current_user)):
    urls = await generate_urls(keys)

    return urls
