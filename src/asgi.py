from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
from src.controllers.tasks import tasks

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

digital_staff.include_router(tasks)

digital_staff.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"]
)


@digital_staff.get("/", include_in_schema=False)
async def docs_redirect():
    return RedirectResponse(url="/docs")
