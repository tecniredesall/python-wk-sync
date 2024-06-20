from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from worker.trumodity.tasks import trumodity_app

router = APIRouter(
    prefix="/contracts",
    tags=["trumodity contracts"],
    responses={404: {"description": "Not found"}},
)


@router.post("/", status_code=200)
def sync_contracts():
    try:
        task = trumodity_app.send_task("worker.trumodity.tasks.get_trumodity_contracts", args=[])
        return JSONResponse({"message": "Syncing the contracts"})
    except Exception as err:
       return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"errors": err.args})
