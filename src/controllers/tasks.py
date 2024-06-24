from typing import List
from fastapi import APIRouter, Form, BackgroundTasks, UploadFile, File
from pydantic import parse_obj_as
from src.models.request_models import CodeFileList
from src.services.no_repo_tasks import manager_development_base_service, no_repo_agent_task_service, \
    no_repo_produce_solution
from src.services.tasks import (
    get_repo_service,
    create_plan_service,
    agent_task_service,
    produce_solution_service,
    process_changes, show_all_changes, add_commit_push
)
from src.utilities.general import cleanup_cloned_repo, delete_folder

tasks = APIRouter(
    prefix="/Tasks",
    responses={
        200: {"description": "Successful"},
        400: {"description": "Bad Request"},
        403: {"description": "Unauthorized"},
        500: {"description": "Internal Server Error"}
    },
    tags=["Agent Tasking"]
)

default_user_prompt = "Refactor the provided code for any vulnerabilities, optimizations, and mistakes."
default_branch = "master"
default_new_branch = "feature/digitalstaff"
default_flow = "no"
default_repo_dir = "./efs/pythongit"
default_agent_task = "Dev 2: responsible for reviewing dev 1 code enhancements"
default_agent_responses = "[Dev 1: Dev 1 response]"


@tasks.post("/repo_ops")
async def repo_task(
        user_prompt: str = Form(default=default_user_prompt, description="What you want the agent to do."),
        https_clone_link: str = Form(description="HTTPs URL to clone your repo."),
        original_code_branch: str = Form(default=default_branch, description="The branch you want to work on."),
        new_branch_name: str = Form(default=default_new_branch,
                                    description="Name for the new branch where changes will be reflected."),
        flow: str = Form(default=default_flow, description="Automated process flow yes/no")
):
    return await get_repo_service(user_prompt, https_clone_link, original_code_branch, new_branch_name, flow)


@tasks.post("/manager_plan")
async def manager_plan(
        user_prompt: str = Form(default=default_user_prompt, description="What you want the agent to do."),
        file_list: str = Form(description="File List given by repo_ops API"),
        original_code_branch: str = Form(default=default_branch, description="The branch you want to work on."),
        new_branch_name: str = Form(default=default_new_branch,
                                    description="Name for the new branch where changes will be reflected."),
        flow: str = Form(default=default_flow, description="Automated process flow yes/no"),
        repo_dir: str = Form(default=default_repo_dir, description="Repo directory folder"),
        file: UploadFile = File(default=None, description="The file attached")
):
    if file_list != "none":
        return await create_plan_service(user_prompt, file_list, repo_dir, new_branch_name, flow)
    else:
        return await manager_development_base_service(user_prompt, file)


@tasks.post("/agent_task")
async def agent_tasks(
        user_prompt: str = Form(default=default_user_prompt, description="What you want the agent to do."),
        file_list: str = Form(description="File List given by repo_ops API"),
        agent_task: str = Form(default=default_agent_task, description="The assigned digital agent's task"),
        new_branch_name: str = Form(default=default_new_branch,
                                    description="Name for the new branch where changes will be reflected."),
        flow: str = Form(default=default_flow, description="Automated process flow yes/no"),
        repo_dir: str = Form(default=default_repo_dir, description="Repo directory folder"),
        agent_responses: str = Form(default=default_agent_responses, description="Agent responses"),
        code: str = Form(default="", description="Generated Code If there is no repo")
):
    if repo_dir != "none":
        parsed_file_list = parse_obj_as(List[str], file_list.split(','))
        return await agent_task_service(agent_task, user_prompt, parsed_file_list, repo_dir, new_branch_name, "",
                                    agent_responses, flow)
    return await no_repo_agent_task_service(agent_task, agent_responses, code)


@tasks.post("/produce_solution")
async def produce_solution(
        user_prompt: str = Form(default=default_user_prompt, description="What you want the agent to do."),
        file_list: str = Form(description="File List given by repo_ops API"),
        new_branch_name: str = Form(default=default_new_branch,
                                    description="Name for the new branch where changes will be reflected."),
        flow: str = Form(default=default_flow, description="Automated process flow yes/no"),
        repo_dir: str = Form(default=default_repo_dir, description="Repo directory folder"),
        agent_responses: str = Form(default=default_agent_responses, description="Agent responses"),
        code: str = Form(default="", description="Generated Code If there is no repo")
):
    if repo_dir != "none":
        parsed_file_list = parse_obj_as(List[str], file_list.split(','))
        return await produce_solution_service(user_prompt, parsed_file_list, repo_dir, new_branch_name, agent_responses, "", flow)
    return await no_repo_produce_solution(user_prompt, file_list, agent_responses, code)


@tasks.post("/show_diff")
async def diff(
        final_artifact: CodeFileList
):
    return await show_all_changes(final_artifact)


@tasks.post("/push_changes")
async def push(
        bg_task: BackgroundTasks,
        commit_message: str = Form(default="Commit by Digital Staff"),
        repo_dir: str = Form(description="The repo directory as stored in efs/repos/<repo>")
):
    push_status = await add_commit_push(commit_message, repo_dir)
    # bg_task.add_task(delete_folder, repo_dir)
    return push_status

@tasks.post("/build_test")
async def build_test(final_artifact: CodeFileList):
    return await process_changes(final_artifact)
