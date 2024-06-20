from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse
from typing import Optional
from app.controllers.farms import (
    get_farms_by_producer,
    get_farms_apps_data_by_producer
)
from app.models.farms import FarmsAppsPayloadModel
from app.models.producers import ProducerDataByApps

router = APIRouter(
    prefix="/farms",
    tags=["farms"],
    responses={404: {"description": "Not found"}},
)

@router.get(
    "/producers/{producer_id}",
    responses={
        status.HTTP_200_OK: {
            "description": "Farm listing",
            "content": {
                "application/json": {
                    "example": {
                        "status": "integer",
                        "data": [
                            "Farm listing"
                        ],
                    "filters": {
                        "producer": "boolean",
                        "farm": "boolean"
                    }}
                }
            },
        },
    }
)
async def list_farms_by_producer(
        producer_id: str, farm_name: Optional[str] = None):
    '''
    List all the farms of a producer by: id or farm name.
    - **producer_id** (required): List all the farms found directly associated with the producer.
    - **farm_name** (optional): searches for any consideration found in the name of any farms.
    '''
    try:
        response = await get_farms_by_producer(producer_id, farm_name)
        return JSONResponse(status_code=response["status"], content=response)
    except Exception as err:
       return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"errors": err.args})


@router.get("/apps", response_model=FarmsAppsPayloadModel, response_model_exclude_none=True)
async def list_farms_apps_data_by_producer(params: ProducerDataByApps = Depends()):
    '''
    The search is carried out by one of the three parameters or all (identity, email, telephone) for producers, being at least one mandatory,
    if it finds a match, an object is returned with the information found from those farms on any platform found in federation owned by the producer.
    '''
    try:
        response = await get_farms_apps_data_by_producer(params)
        return response
    except Exception as err:
       return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"errors": err.args})
