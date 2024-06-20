import re

from bson import ObjectId
from datetime import datetime
from fastapi import APIRouter, Body, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Any

from ..models.pyobjectid import PyObjectId
from lib.database import MongoManagerAsync

router = APIRouter(
    prefix="/actions",
    tags=["actions"],
    responses={404: {"description": "Not found"}},
)
client = MongoManagerAsync().client
db = client['worker_sync']


# Action class defined in Pydantic
class ActionModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    action: str
    active: bool
    created: datetime
    parent: PyObjectId = Field(default_factory=PyObjectId)
    schedule: Optional[str]
    payload: Optional[Any]

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class UpdateActionModel(BaseModel):
    parent: Optional[str]
    schedule: Optional[str]
    payload: Optional[Any]

    class Config:
        schema_extra = {
            "example": {
                "parent": "",
                "schedule": 'hour=7, minute=30'
            }
        }


@router.get(
    "/", response_description="List action catalog", response_model=List[ActionModel]
)
async def list_actions():
    actions = await db.actions.find().to_list(1000)
    return actions


@router.put(
    "/{id}",
    response_description="Configure action",
    response_model=ActionModel,
    description="See schedule documentation in https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html#crontab-schedules"
)
async def cofigure_action(id: str, action: UpdateActionModel = Body(...)):
    try:
        ObjectId(id)
    except Exception as err:
       return JSONResponse(status_code=404, content={"errors": ['ID not found']})
    try:
        ObjectId(action['parent'])
    except Exception as err:
       return JSONResponse(status_code=404, content={"errors": ['Parent ID not found']})
    if (item := await db.actions.find_one({"_id": ObjectId(id)})) is not None:
        action = {k: v for k, v in action.dict().items() if v is not None}
        updateData = {'$set': {}, '$unset': {}}
        if 'parent' not in action or ('parent' in action and action['parent'] == ''):
            updateData['$unset']['parent'] = 1
            del action['parent']
        if 'schedule' not in action or ('schedule' in action and action['schedule'] == ''):
            updateData['$unset']['schedule'] = 1
            del action['schedule']
        if 'schedule' in action:
            action['schedule'] = action['schedule'] if re.match(r'^(\d)+(\.(\d)+)?$', action['schedule']) else f"crontab({action['schedule']})"
        if 'parent' in action:
            action['parent'] = ObjectId(action['parent'])
            if (parent_item := await db.actions.find_one({"_id": action['parent']})) is None:
                raise HTTPException(status_code=404, detail=f"Parent action {action['parent']} not found")
        updateData['$set'] = action
        if(updateData['$set'] == {}): del updateData['$set']
        if(updateData['$unset'] == {}): del updateData['$unset']
        update_item = await db.actions.update_one({"_id": ObjectId(id)}, updateData)
        if update_item.modified_count == 1:
            if (
                updated_item := await db.actions.find_one({"_id": ObjectId(id)})
            ) is not None:
                return updated_item
        if (existing_action := await db.actions.find_one({"_id": ObjectId(id)})) is not None:
            return existing_action
        # TODO: update beat service
    else:
        raise HTTPException(status_code=404, detail=f"Action {id} not found")


@router.patch(
    "/{id}", response_description="Update action status"
)
async def update_status(id: str, active: bool):
    try:
        ObjectId(id)
    except Exception as err:
       return JSONResponse(status_code=404, content={"errors": ['ID not found']})
    await db.actions.update_one(
            {"_id": ObjectId(id) }, 
            {'$set': { "active": active }}
        )
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content={'id': id, 'active':active})
