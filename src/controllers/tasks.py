import platform
import subprocess
import uuid
from fastapi import APIRouter, Form
from typing import List
from pydantic import parse_obj_as

from src.models.request_models import RequestModel
from src.services.tasks import get_repo_service, create_plan_service, agent_task_service, produce_solution_service

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
        user_prompt: str = Form(
            description="What you want the agent to do.",
            default="Refactor the provided code for any vulnerabilities, optimizations, and mistakes."
        ),
        new_branch_name: str = Form(
            default="feature/digitalstaff",
            description="Name for the new branch where changes will be reflected."
        ),
        flow: str = Form(default="no", description="automated process flow yes/no"),
        repo_dir: str = Form(default="./efs/pythongit", description="repo directory folder"),
        agent_responses: str = Form(default="[Dev 1: Dev 1 response]", description="agent responses")
):
    return await run_python_tests("efs/repos/VideoPlayer_Consumer_Producer")


async def identify_language(repo_dir):
    NotImplemented


async def run_python_tests(repo_dir):
    # virtualenv venv
    # .\venv\Scripts\activate
    # pip install pytest pytest-cov httpx
    # pip install -r requirements.txt
    # pytest -p no:cacheprovider --cov=.
    # issue correction loops
    # deactivate the venv
    # cleanup venv files
    unique_venv_name = f"{uuid.uuid4().hex[:6].upper()}"
    install_testing_env = subprocess.Popen(
        f"virtualenv {unique_venv_name}".split(),
        cwd=f"./{repo_dir}",
        stdout=subprocess.PIPE
    )
    if "created" in install_testing_env.communicate()[0].decode('utf-8'):
        print(f"{unique_venv_name} created")
        venv_deactivate_command = "deactivate"
        if "Windows" in platform.system():
            venv_activate_command = f'.\\{unique_venv_name}\\Scripts\\activate'
            path_to_python_exec = f'{unique_venv_name}\\Scripts\\python.exe'
        else:
            venv_activate_command = f"source {unique_venv_name}/bin/activate"
            path_to_python_exec = f'{unique_venv_name}/bin/python'
        activate_virtual_env = subprocess.Popen(
            venv_activate_command.split(),
            cwd=f"./{repo_dir}",
            stdout=subprocess.PIPE,
            shell=True
        )
        activate_virtual_env.wait()

        if "cannot" not in activate_virtual_env.communicate()[0].decode('utf-8'):
            print(f"{unique_venv_name} activated")
            install_testing_dependencies = subprocess.Popen(
                f"{path_to_python_exec} -m pip install pytest pytest-cov httpx".split(),
                cwd=f"./{repo_dir}",
                stdout=subprocess.PIPE,
                shell=True
            )
            install_testing_dependencies.wait()
            if "installed" in install_testing_dependencies.communicate()[0].decode('utf-8'):
                print("pytest deps installed")
                install_repo_requirements = subprocess.Popen(
                    f"{path_to_python_exec} -m pip install -r requirements.txt".split(),
                    cwd=f"./{repo_dir}",
                    stdout=subprocess.PIPE,
                    shell=True
                )
                install_repo_requirements.wait()
                print("Completed installation of requirements")
                return install_repo_requirements.communicate()[0].decode('utf-8')
