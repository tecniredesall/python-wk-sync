from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.models.settings import get_settings
from .routers import actions
from .routers import blocks
from .routers import contracts
from .routers import farms
from .routers import pendingactions
from .routers import producers
from .routers import secure
from .routers import testingtasks
from .routers import trumoditytest

config = get_settings()

tags_metadata = [
    {
        "name": "actions",
        "description": "Pending actions catalog",
    },
    {
        "name": "API",
        "description": "In order to see if the application is running ok you can invoke this endpoint.",
    },
    {
        "name": "blocks",
        "description": "Sync blocks",
    },
    {
        "name": "farms",
        "description": "Sync farms",
    },
    {
        "name": "pending actions",
        "description": "Sync pending actions functionality",
    },
    {
        "name": "producers",
        "description": "Sync producers",
    },
    {
        "name": "worker test",
        "description": "Operations with worker testing.",
    },
    {
        "name": "trumodity contracts",
        "description": "Sync trumodity contracts functionality",
    },
    {
        "name": "trumodity test",
        "description": "Operations with trumodity testing.",
    },
]

app = FastAPI(
    title="Worker Sync",
    description="This is the Worker Sync project",
    version="0.1.0",
    openapi_tags=tags_metadata,
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ALLOWED_ORIGINS,
    allow_credentials=config.CORS_ALLOW_CREDENTIALS,
    allow_methods=config.CORS_ALLOW_METHODS,
    allow_headers=config.CORS_ALLOW_HEADERS,
)
#app.mount("/static", StaticFiles(directory="static"), name="static")
#templates = Jinja2Templates(directory="templates")

@app.get("/", tags=["API"])
async def welcome():
    return {"message": "This is where the awesomeness happen..."}

app.include_router(actions.router)
app.include_router(blocks.router)
app.include_router(contracts.router)
app.include_router(farms.router)
app.include_router(pendingactions.router)
app.include_router(producers.router)
app.include_router(secure.router)
app.include_router(testingtasks.router)
app.include_router(trumoditytest.router)

if __name__ == '__main__':
    uvicorn.run('main:app', reload=True, debug=True, host='0.0.0.0', port=5000, log_level="info")
