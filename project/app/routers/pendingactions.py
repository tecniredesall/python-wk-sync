from bson import ObjectId
from datetime import datetime
from fastapi import APIRouter, HTTPException, Body, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Any

from ..models.pendingActionRequest import PendingAction
from ..models.pyobjectid import PyObjectId
from lib.database import MongoManagerAsync
from worker.pendingactions.tasks import worker

router = APIRouter(
    prefix="/pending-actions",
    tags=["pending actions"],
    responses={404: {"description": "Not found"}},
)
client = MongoManagerAsync().client
db = client['worker_sync']


class PendingActionModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    action: str
    parent: Optional[str]
    request_payload: Optional[Any]
    response_payload: Optional[Any]
    consumed: bool
    successful: Optional[bool]
    received: datetime

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


@router.get(
    "/", response_description="List pending actions", response_model=List[PendingActionModel]
)
async def list_pendingactions():
    pendingactions = await db.pendingactions.find().to_list(100)
    return pendingactions


@router.get(
    "/{id}", response_description="Get a single pending action", response_model=PendingActionModel
)
async def show_pendingaction(id: str):
    if (pendingaction := await db.pendingactions.find_one({"_id": ObjectId(id)})) is not None:
        return pendingaction

    raise HTTPException(status_code=404, detail=f"Pending action {id} not found")


@router.post("/", response_description="Request a pending action", response_model=PendingActionModel)
async def request_pending_action(pendingaction: PendingAction = Body(...)):
    try:
        pendingaction = jsonable_encoder(pendingaction)
        actionCounter = await db.actions.count_documents({
            "action" : pendingaction['action'],
            "active" : False,
        })
        if(actionCounter == 0):
            pendingaction.update({
                'received': datetime.now(),
                'consumed': False
            })
            worker.send_task("worker.pendingactions.tasks.consume_pending_actions", args=[pendingaction['action'], pendingaction['request_payload']])
            return JSONResponse(status_code=201, content={'status':'true'})
    except Exception as err:
       return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"errors": err.args})


@router.post("/run", response_description="Run pending actions")
async def run_pending_actions():
    worker.send_task("worker.pendingactions.tasks.consume_pending_actions", args=[])
    return JSONResponse(status_code=200, content={'success': 'true'})
