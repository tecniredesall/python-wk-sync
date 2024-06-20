from fastapi import APIRouter, Depends

from app.auth.auth_bearer import JWTBearer

router = APIRouter(
    prefix="/secure",
    tags=["secure"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", dependencies=[Depends(JWTBearer())])
async def secure_post_request() -> dict:
    return {
        "data": "post request"
    }


@router.get("/", dependencies=[Depends(JWTBearer())])
async def secure_get_request() -> dict:
    return {
        "data": "get request"
    }