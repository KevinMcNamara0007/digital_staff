from typing import List, Dict, Any

from pydantic import BaseModel


class Artifacts(BaseModel):
    repo_url: str
    latest_commit: str
    files_changed: List[str]
    issues_found: List[str]
    additional_data: Dict[str, Any] = {}


class RequestModel(BaseModel):
    prompt_instructions: str
    artifacts: Artifacts


class CodeFile(BaseModel):
    FILE_NAME: str
    FILE_CODE: str


class CodeFileList(BaseModel):
    repo_dir: str
    produced_code: List[CodeFile]
