import pika
import json

from app.models.settings import get_settings

from bson import ObjectId
from datetime import datetime
from fastapi import APIRouter, HTTPException, Body, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List

from ..models.pyobjectid import PyObjectId
from lib.database import MongoManagerAsync

router = APIRouter(
    prefix="/trumodity-test",
    tags=["trumodity test"],
    responses={404: {"description": "Not found"}},
)
client = MongoManagerAsync().client
db = client['worker_sync']

class MessagesModel(BaseModel):
    status: Optional[str]
    received: datetime


class SettlingProcessModel(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    purchase_order_id: str
    status: Optional[str]
    messages: Optional[List[MessagesModel]]

    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class PaymentTypesModel(BaseModel):
    concept: str
    account: Optional[str]
    amount: float


class MovementsModel(BaseModel):
    account: Optional[str]
    concept: str
    type: str
    total: float


class UpdateSettlingProcessModel(BaseModel):
    status: str
    movements: Optional[List[MovementsModel]]
    payment_types: Optional[List[PaymentTypesModel]]
    subtotal: Optional[float]
    total: Optional[float]
    settled_at: Optional[str]
    partition_key: str

    class Config:
        schema_extra = {
            "example": {
                "status": "received",
            }
        }


@router.get(
    "/settling_processes",
    response_description="List settling processes",
    response_model=List[SettlingProcessModel]
)
async def list_settling_processes():
    return await db.settling_processes.find().to_list(100)


@router.post("/settling_processes/{id}", response_description="Change settling status")
async def change_settilg_status(id: str, body_request: UpdateSettlingProcessModel = Body(...)):
    try:
        if (item := await db.settling_processes.find_one({"_id": ObjectId(id)})) is not None:
            config = get_settings()
            message = json.loads(body_request.json())
            message.update({"process_id": id})
            credentials = pika.PlainCredentials(config.GC_RABBIT_USERNAME, config.GC_RABBIT_PASSWORD)
            connection = pika.BlockingConnection(pika.ConnectionParameters(config.GC_RABBIT_HOST,
                    config.GC_RABBIT_PORT,
                    '/',
                    credentials
            ))
            channel = connection.channel()
            channel.queue_declare(queue=config.GC_RABBIT_QUEUE)
            channel.queue_bind(
                queue=config.GC_RABBIT_QUEUE,
                exchange=config.GC_RABBIT_EXCHANGE,
                routing_key=config.GC_RABBIT_ROUTING_KEY
            )
            channel.basic_publish(
                exchange=config.GC_RABBIT_EXCHANGE,
                routing_key=config.GC_RABBIT_ROUTING_KEY,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode = 2, # make message persistent
                )
            )
            connection.close()
            return JSONResponse(status_code=202, content={'success':'true'})
        else:
            raise HTTPException(status_code=404, detail=f"Action {id} not found")
    except Exception as err:
       return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"errors": err.args})
