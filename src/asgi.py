from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from src.controllers.developer_controller import tasks
from src.controllers.data_controller import data
from src.controllers.content_controller import content
from fastapi.staticfiles import StaticFiles

# App Details
digital_staff = FastAPI(
    title="Digital Staff Backend",
    summary="Delegate tasks to Agents",
    version="1",
    swagger_ui_parameters={
        "syntaxHighlight.theme": "obsidian",
        "docExpansion": "none"
    }
)
digital_staff.mount("/digital_staff", StaticFiles(directory="static", html=True), name="static")
digital_staff.include_router(tasks)
digital_staff.include_router(data)
digital_staff.include_router(content)

digital_staff.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"]
)


@digital_staff.get("/", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(url="/digital_staff")
