from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse
from typing import Optional
from app.controllers.blocks import (
    get_blocks_by_producer,
    get_blocks_apps_data_by_producer
)
from app.models.producers import ProducerDataByApps
from app.models.blocks import BlocksAppsPayloadModel

router = APIRouter(
    prefix="/blocks",
    tags=["blocks"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/producers/{producer_id}",
    responses={
        status.HTTP_200_OK: {
            "description": "Block listing",
            "content": {
                "application/json": {
                    "example": {"data": ["Block listing"], "filters": {
                        "producer": "boolean",
                        "farm": "boolean",
                        "block": "boolean"
                    }}
                }
            },
        },
    }
)
async def list_blocks_by_producer(
        producer_id: str, farm_id: Optional[str] = None, block_name: Optional[str] = None):
    '''
    List all the blocks of a producer by: id, farm id or block name.
    - **producer_id** (required): List all the blocks found within the farms or blocks directly associated with the producer.
    - **farm_id** (optional): Find the blocks that belong to that farm only.
    - **block_name** (optional): searches for any consideration found in the name of any block.
    '''
    try:
        response = await get_blocks_by_producer(producer_id, block_name, farm_id)
        return JSONResponse(status_code=response["status"], content=response)
    except Exception as err:
       return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"errors": err.args})


@router.get("/apps", response_model=BlocksAppsPayloadModel, response_model_exclude_none=True)
async def list_blocks_apps_data_by_producer(params: ProducerDataByApps = Depends()):
    '''
    The search is carried out by one of the three parameters or all (identity, email, telephone) for producers, being at least one mandatory,
    if it finds a match, an object is returned with the information found from those blocks on any platform found in federation owned by the producer.
    '''
    try:
        response = await get_blocks_apps_data_by_producer(params)
        return response
    except Exception as err:
       return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"errors": err.args})
