from fastapi import APIRouter, Form, UploadFile, File

from src.services.data_services import data_annotator_service

data = APIRouter(
    prefix="/Data",
    responses={
        200: {"description": "Successful"},
        400: {"description": "Bad Request"},
        403: {"description": "Unauthorized"},
        500: {"description": "Internal Server Error"}
    },
    tags=["Annotation"]
)


@data.post("/data_annotator")
async def data_annotator(
        description: str = Form(default="Create 10-20 worded stories", description="description of the type of data you want to generate"),
        rows: int = Form(description="The amount of rows you want"),
        labels: str = Form(default="[{'label':'labelValue1'},{'label':'labelValue2'}]", description="Object Array of Labels and Description")
):
    return await data_annotator_service(description, rows, labels)