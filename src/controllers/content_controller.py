from fastapi import APIRouter, Form, UploadFile, File, Query

from src.services.content_services import peer_review_service, final_draft_service

content = APIRouter(
    prefix="/Content",
    responses={
        200: {"description": "Successful"},
        400: {"description": "Bad Request"},
        403: {"description": "Unauthorized"},
        500: {"description": "Internal Server Error"}
    },
    tags=["Content Formatting"]
)


@content.post("/review")
async def content_reviewer(
        original: str = Form(default="", description="original content"),
        style: str = Form(default="", description="AP/NYT"),
        persona: str = Form(default="", description="Professional/Creative/Comedic/Formal/None"),
        model: str = Form(default="elf", description="Model ELF/OAI")
):
    return await peer_review_service(original, style, persona, model)


@content.post("/final_draft")
async def content_reviewer(
        original: str = Form(default="", description="original content"),
        style: str = Form(default="", description="AP/NYT"),
        review: str = Form(default="", description="Peer Review"),
        persona: str = Form(default="", description="Professional/Creative/Comedic/Formal/None"),
        model: str = Form(default="elf", description="Model ELF/OAI")
):
    return await final_draft_service(original, style, persona, review, model)
