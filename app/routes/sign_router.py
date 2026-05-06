from fastapi import APIRouter, Body, Depends, Form
from fastapi.responses import JSONResponse

from app.depends.auth_deps import get_current_user
from app.models.sign_style import SignatureStyle
from app.services.sign_service import (
    delete_sign_response,
    edit_name_response,
    finalize_sign_upload_response,
    generate_sign_response,
    get_sign_outline_response,
    get_sign_url_response,
    get_signs_by_status_response,
    hard_delete_sign_response,
    restore_sign_response,
)


router = APIRouter()


def _json_response(payload: dict) -> JSONResponse:
    return JSONResponse(
        content=payload,
        headers={"Connection": "close"},
    )


@router.post("/request")
async def generate_sign(
    name: str | None = Form(None),
    style: SignatureStyle = Form(SignatureStyle.LUXURY),
    seed: int | None = Form(None),
):
    response = await generate_sign_response(name, style, seed)

    return _json_response(response)


@router.post("/upload")
async def finalize_sign_upload(
    temp_file_name: str = Form(), user=Depends(get_current_user)
):
    return await finalize_sign_upload_response(temp_file_name, user)


@router.get("/list")
async def get_signs_by_status(
    is_deleted: bool, user=Depends(get_current_user)
):
    signs = await get_signs_by_status_response(user, is_deleted)

    return {"status": 200, "signs": signs}


@router.patch("/name")
async def edit_sign_name(
    sign_id: str = Form(),
    new_name: str = Form(),
    user=Depends(get_current_user),
):
    edited_sign = await edit_name_response(user, sign_id, new_name)

    return {"status": 200, "editedSign": edited_sign}


@router.delete("/soft")
async def delete_sign(
    sign_id: str = Body(..., embed=True),
    user=Depends(get_current_user),
):
    deleted_sign = await delete_sign_response(user, sign_id)

    return {"status": 200, "deletedSign": deleted_sign}


@router.post("/restore")
async def restore_sign(
    sign_id: str = Body(..., embed=True),
    user=Depends(get_current_user),
):
    restored_sign = await restore_sign_response(user, sign_id)

    return {"status": 200, "restoredSign": restored_sign}


@router.delete("/hard")
async def hard_delete_sign(
    sign_id: str = Body(..., embed=True),
    user=Depends(get_current_user),
):
    return await hard_delete_sign_response(user, sign_id)


@router.get("/sign/{sign_id}")
async def get_sign(sign_id: str, user=Depends(get_current_user)):
    url = await get_sign_url_response(user, sign_id)

    return {"status": 200, "url": url}


@router.get("/outline/{sign_id}")
async def get_sign_outline(
    sign_id: str, width: int, height: int, user=Depends(get_current_user)
):
    outline = await get_sign_outline_response(user, sign_id, width, height)

    return {"status": 200, **outline}
