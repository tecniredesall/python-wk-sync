from fastapi import APIRouter, status, Depends
from fastapi.responses import JSONResponse
from app.controllers.producers import (
    validate_producer_data,
    get_producer_apps_data
)
from app.models.producers import (
    ProducerIncomingPayloadSchema,
    ProducerDataByApps,
    ProducerAppsPayloadModel
)

router = APIRouter(
    prefix="/producers",
    tags=["producers"],
    responses={404: {"description": "Not found"}},
)

@router.post("/verify",
             responses={
        status.HTTP_200_OK: {
            "description": "Block listing",
            "content": {
                "application/json": {
                    "example": {
                        "status": "status code",
                        "message": "string",
                        "pendingAction": "boolean",
                        "data": "object."
                    }
                }
            },
        },
    }
)
async def producer_verification(producer_payload: ProducerIncomingPayloadSchema):
    '''
    Check if the producer exists by means of: identifier (mandatory), RTN or producer id. It is verified if it is sent, 
    the email and the telephone, if in the records of other producers it exists, if it is not used by others,
    a pending action is sent so that it is sent to the federation to create or update the producer's data that was sent.
    If it finds the producer in data, it returns the information found and the status will be 200, if it cannot find it, the status will be 404.
    If the pending action creation was successful, a 'True' is sent in the pendingAction variable, otherwise 'False'.
    '''
    try:
        response = await validate_producer_data(producer_payload)
        return JSONResponse(status_code=response['status'], content=response)
    except Exception as err:
       return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"errors": err.args})


@router.get("/apps", response_model=ProducerAppsPayloadModel, response_model_exclude_none=True)
async def list_producer_apps_data(params: ProducerDataByApps = Depends()):
    '''
    The search is carried out by one of the three parameters or all (identity, email, phone), being at least one mandatory, 
    if it finds a match, an object is returned with the information found from that producer on any platform kept in federation.
    '''
    try:
        response = await get_producer_apps_data(params)
        return response
    except Exception as err:
       return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"errors": err.args})
