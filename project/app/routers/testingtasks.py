from celery.result import AsyncResult
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from worker.main import create_task

from ..models.testtask import TestTask

router = APIRouter(
    prefix="/tasks",
    tags=["worker test"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", status_code=201)
def run_task(testTask: TestTask):
    task = create_task.delay(testTask.type)
    return JSONResponse({"task_id": task.id})


@router.get("/{task_id}")
def get_status(task_id):
    task_result = AsyncResult(task_id)
    result = {
        "task_id": task_id,
        "task_status": task_result.status,
        "task_result": task_result.result
    }
    return JSONResponse(result)
