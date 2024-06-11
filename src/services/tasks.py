import os.path
import platform
import shutil
import uuid
from src.utilities.general import file_filter, cleanup_post_test
from src.utilities.git import clone_repo, check_current_branch, checkout_and_rebranch, repo_file_list, \
    show_file_contents, cmd_popen, cmd_run
from src.utilities.inference2 import manager__development_agent_prompts, agent_task, produce_final_solution
import src.utilities.inference2


async def get_repo_service(user_prompt, https_clone_link, original_code_branch, new_branch_name, flow="n"):
    repo_dir = await clone_repo(https_clone_link)
    cur_branch = await check_current_branch(repo_dir)
    if cur_branch not in new_branch_name or new_branch_name not in cur_branch:
        _ = await checkout_and_rebranch(new_branch_name, original_code_branch, repo_dir)
    file_list = await repo_file_list(repo_dir)
    file_list = file_filter(file_list)
    if flow == "y":
        await create_plan_service(user_prompt, file_list, repo_dir, new_branch_name, flow)
    return {"user_prompt": user_prompt, "files": file_list, "repo_dir": repo_dir}


async def create_plan_service(user_prompt, file_list, repo_dir, new_branch_name, flow="n"):
    if flow == "y":
        tasks = manager__development_agent_prompts(user_prompt, file_list)
        # Get All Code Into 1 string
        all_code = await get_all_code(file_list, repo_dir, new_branch_name)
        # Do Each Agent Task
        all_agent_responses = ""
        for index, agent_prompt in enumerate(tasks):
            print(agent_prompt)
            agent_response = await agent_task_service(agent_prompt, user_prompt, file_list, repo_dir, new_branch_name,
                                                      all_code, all_agent_responses, flow)
            all_agent_responses = all_agent_responses + "{" f"Agent: {index}, Response: {agent_response}" "}"
        # get final solution
        return await produce_solution_service(user_prompt, file_list, repo_dir, new_branch_name, all_agent_responses, all_code, flow)
    return manager__development_agent_prompts(user_prompt, file_list)


async def agent_task_service(task, user_prompt, file_list, repo_dir, new_branch_name, code="", response="", flow="n"):
    if flow == "y":
        response = await src.utilities.inference2.agent_task(task, response, code)
        print(response)
        return response
    # Get All Code
    all_code = await get_all_code(file_list, repo_dir, new_branch_name)
    return await src.utilities.inference2.agent_task(task, response, all_code)


async def get_all_code(file_list, repo_dir, new_branch_name):
    all_code = ""
    for file in file_list:
        file_code = await show_file_contents(new_branch_name, file, repo_dir)
        all_code = all_code + f"\n### *File Name: {file}* *File Code: {file_code}*###"
    return all_code


async def produce_solution_service(user_prompt, file_list, repo_dir, new_branch_name,
                                   agent_responses, code="", flow="n"):
    if code == "":
        code = await get_all_code(file_list, repo_dir, new_branch_name)
    return await src.utilities.inference2.produce_final_solution(user_prompt, file_list, agent_responses, code)


async def run_python_tests(repo_dir, present_venv_name=None, tries=3):
    """
    Takes the local path of the repo, an existing venv, and number of tries. It creates/reuses a venv to run pytest on
    any possible tests that may be present in the repo. If any errors arise, it will fix them and rerun the tests.
    :param repo_dir:
    :param present_venv_name:
    :param tries:
    :return:
    """
    unique_venv_name = f"{uuid.uuid4().hex[:6].upper()}" if not present_venv_name else present_venv_name
    # Create virtual env
    await cmd_run(
        command_to_run=f"virtualenv {repo_dir}/{unique_venv_name}",
    )
    path_to_python_exec = f'{unique_venv_name}\\Scripts\\python.exe' \
        if "Windows" in platform.system() \
        else f'{unique_venv_name}/bin/python'
    # Install all dependencies + requirements of repo
    await cmd_popen(
        repo_dir=repo_dir,
        command_to_run=f"{path_to_python_exec} -m pip install pytest pytest-cov httpx -r requirements.txt",
        shelled=True
    )
    # Run tests
    test_output = await cmd_popen(
        repo_dir=repo_dir,
        command_to_run=f"{path_to_python_exec} -m pytest -p no:cacheprovider --no-cov",
        shelled=True
    )
    # issue correction loops
    if "FAILED" in test_output or "Interrupted" in test_output:
        await failure_repair(test_output, repo_dir, unique_venv_name, tries)
    # Cleanup
    await cleanup_post_test(venv_name=unique_venv_name, repo_dir=repo_dir)
    return "Success"


async def failure_repair(output_message, repo_dir, venv_name, tries=3):
    """
    Fixes errors that come up during the run of the testing phases dependent on the error returned from the pytest
    command.
    :param output_message:
    :param repo_dir:
    :param venv_name:
    :param tries:
    :return:
    """
    # Check for missing packages
    if "No module named" in output_message:
        start = output_message.index("No module named")
        missing_package = output_message[start:].split("'")[1]
        # Add package to requirements file
        with open(f"{repo_dir}\\requirements.txt", "a") as f:
            f.write("\n" + missing_package + "\n")
        return await run_python_tests(repo_dir, venv_name, tries - 1) \
            if tries > 0 else RuntimeError(f"Failed to add package: {missing_package}")
    return "LLM Needs to be involved here"
