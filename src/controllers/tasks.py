from typing import List
from fastapi import APIRouter, Form
from pydantic import parse_obj_as
from src.services.tasks import get_repo_service, create_plan_service, agent_task_service, produce_solution_service, \
    run_python_tests

tasks = APIRouter(
    prefix="/Tasks",
    responses={
        200: {
            "description": "Successful"
        },
        400: {
            "description": "Bad Request"
        },
        403: {
            "description": "Unauthorized"
        },
        500: {
            "description": "Internal Server Error"
        }
    },
    tags=["Agent Tasking"]
)


@tasks.post("/repo_ops")
async def repo_task(
        user_prompt: str = Form(
            description="What you want the agent to do.",
            default="Refactor the provided code for any vulnerabilities, optimizations, and mistakes."
        ),
        https_clone_link: str = Form(
            description="HTTPs URL to clone your repo."
        ),
        original_code_branch: str = Form(
            default="master",
            description="The branch you want to work on."
        ),
        new_branch_name: str = Form(
            default="feature/digitalstaff",
            description="Name for the new branch where changes will be reflected."
        ),
        flow: str = Form(
            default="no",
            description="automated process flow yes/no"
        )
):
    return await get_repo_service(user_prompt, https_clone_link, original_code_branch, new_branch_name, flow)


@tasks.post("/manager_plan")
async def manager_plan(
        user_prompt: str = Form(
            description="What you want the agent to do.",
            default="Refactor the provided code for any vulnerabilities, optimizations, and mistakes."
        ),
        file_list: str = Form(
            description="File List given by repo_ops api"
        ),
        original_code_branch: str = Form(
            default="master",
            description="The branch you want to work on."
        ),
        new_branch_name: str = Form(
            default="feature/digitalstaff",
            description="Name for the new branch where changes will be reflected."
        ),
        flow: str = Form(default="no", description="automated process flow yes/no"),
        repo_dir: str = Form(default="./efs/pythongit", description="repo directory folder")
):
    return await create_plan_service(user_prompt, file_list, repo_dir, new_branch_name, flow)


@tasks.post("/agent_task")
async def agent_tasks(
        user_prompt: str = Form(
            description="What you want the agent to do.",
            default="Refactor the provided code for any vulnerabilities, optimizations, and mistakes."
        ),
        file_list: str = Form(
            description="File List given by repo_ops api"
        ),
        agent_task: str = Form(
            default="Dev 2: responsible for reviewing dev 1 code enhancements",
            description="The assigned digital agents task"
        ),
        new_branch_name: str = Form(
            default="feature/digitalstaff",
            description="Name for the new branch where changes will be reflected."
        ),
        flow: str = Form(default="no", description="automated process flow yes/no"),
        repo_dir: str = Form(default="./efs/pythongit", description="repo directory folder"),
        agent_responses: str = Form(default="[Dev 1: Dev 1 response]", description="agent responses")
):
    file_list = parse_obj_as(List[str], file_list.split(','))
    return await agent_task_service(agent_task, user_prompt, file_list, repo_dir,
                                    new_branch_name, "", agent_responses, flow)


@tasks.post("/produce_solution")
async def produce_solution(
        user_prompt: str = Form(
            description="What you want the agent to do.",
            default="Refactor the provided code for any vulnerabilities, optimizations, and mistakes."
        ),
        file_list: str = Form(
            description="File List given by repo_ops api"
        ),
        new_branch_name: str = Form(
            default="feature/digitalstaff",
            description="Name for the new branch where changes will be reflected."
        ),
        flow: str = Form(default="no", description="automated process flow yes/no"),
        repo_dir: str = Form(default="./efs/pythongit", description="repo directory folder"),
        agent_responses: str = Form(default="[Dev 1: Dev 1 response]", description="agent responses")
):
    file_list = parse_obj_as(List[str], file_list.split(','))
    return await produce_solution_service(user_prompt, file_list, repo_dir,
                                          new_branch_name, agent_responses, "", flow)


@tasks.post("/build_test")
async def build_test(
        repo_dir: str = Form(description="repo directory folder"),
):
    return await run_python_tests(repo_dir)




