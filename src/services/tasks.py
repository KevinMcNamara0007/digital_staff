import importlib
import os
import platform
import re
import uuid
from importlib import metadata

from src.utilities.general import file_filter, cleanup_post_test
from src.utilities.git import clone_repo, check_current_branch, checkout_and_rebranch, repo_file_list, \
    show_file_contents, cmd_popen, cmd_run
from src.utilities.inference2 import manager__development_agent_prompts, agent_task, produce_final_solution, \
    customized_response


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
        #API Get All Code Into 1 string
        all_code = await get_all_code(file_list, repo_dir, new_branch_name)
        #API Do Each Agent Task
        all_agent_responses = ""
        for index, agent_prompt in enumerate(tasks):
            print(agent_prompt)
            agent_response = await agent_task_service(agent_prompt, user_prompt, file_list, repo_dir, new_branch_name,
                                                      all_code, all_agent_responses, flow)
            all_agent_responses = all_agent_responses + "{" f"Agent: {index}, Response: {agent_response}" "}"
        #API get final solution
        return await produce_solution_service(user_prompt, file_list, repo_dir, new_branch_name, all_agent_responses,
                                              all_code, flow)
    #UI Get Software Type
    software_type = await get_software_type(file_list)
    print(f"SOFTWARE TYPE: {software_type}")
    #UI Return Manager Prompts
    return manager__development_agent_prompts(user_prompt, file_list, software_type)


async def agent_task_service(task, user_prompt, file_list, repo_dir, new_branch_name, code="", response="", flow="n"):
    if flow == "y":
        #API FLOW FOR AGENT TASKS
        response = await agent_task(task, response, code)
        print(response)
        return response
    #UI Get All Code
    all_code = await get_all_code(file_list, repo_dir, new_branch_name)
    return await agent_task(task, response, all_code)


async def get_all_code(file_list, repo_dir, new_branch_name):
    all_code = ""
    for file in file_list:
        file_code = await show_file_contents(new_branch_name, file, repo_dir)
        all_code = all_code + f"\n### *File Name: {file}* *File Code: {file_code}*###"
    return all_code


async def get_software_type(assets):
    prompt = f"Respond only with the type of developer made these files {assets}"
    return customized_response(prompt)


async def produce_solution_service(user_prompt, file_list, repo_dir, new_branch_name,
                                   agent_responses, code="", flow="n"):
    if code == "":
        code = await get_all_code(file_list, repo_dir, new_branch_name)
    return await produce_final_solution(user_prompt, file_list, agent_responses, code)


async def run_python_tests(repo_dir, present_venv_name=None, tries=3):
    """
    Takes the local path of the repo, an existing venv, and number of tries. It creates/reuses a venv to run pytest on
    any possible tests that may be present in the repo. If any errors arise, it will fix them and rerun the tests.

    :param repo_dir: Directory of the repository.
    :param present_venv_name: Name of an existing virtual environment.
    :param tries: Number of attempts to retry fixing issues.
    :return: Result of the test run after attempting to fix issues.
    """
    unique_venv_name = present_venv_name or f"{uuid.uuid4().hex[:6].upper()}"

    # Create virtual environment
    await cmd_run(f"virtualenv {os.path.join(repo_dir, unique_venv_name)}")

    path_to_python_exec = os.path.join(unique_venv_name, 'Scripts', 'python.exe') if platform.system() == "Windows" else os.path.join(unique_venv_name, 'bin', 'python')

    # Install dependencies
    await cmd_popen(repo_dir, f"{path_to_python_exec} -m pip install pytest pytest-cov httpx -r requirements.txt", shelled=True)

    # Run tests and analyze results
    results = await run_pytest_and_analyze(repo_dir, path_to_python_exec)
    if results["unknown_packages"]:
        results["missing_packages"].extend(find_official_package_names(results["unknown_packages"]))
    # Check for missing packages or code errors and attempt to fix them
    if results["missing_packages"] or results["code_errors"]:
        await failure_repair(results["missing_packages"], results["code_errors"], repo_dir, unique_venv_name, tries)

    # Cleanup
    # await cleanup_post_test(venv_name=unique_venv_name, repo_dir=repo_dir)

    return "Success"

def find_official_package_names(package_names):
    official_names = []
    for package_name in package_names:
        prompt = (f"What is the official package name for '{package_name}'? "
                  f"Respond with only the official name of the package.")

        response = customized_response(prompt)

        if response:
            official_name = response.strip()
            official_names.append(official_name)
    return official_names


async def failure_repair(missing_packages, code_errors, repo_dir, venv_name, tries=3):
    """
    Fixes errors that come up during the run of the testing phases dependent on the error returned from the pytest
    command.

    :param missing_packages: List of missing packages detected during the pytest run.
    :param code_errors: List of code errors detected during the pytest run.
    :param repo_dir: Directory of the repository.
    :param venv_name: Name of the virtual environment.
    :param tries: Number of attempts to retry fixing the issues.
    :return: Result of the test run after attempting to fix issues.
    """
    # Check for missing packages
    if missing_packages:
        missing_modules = '\n'.join(missing_packages) + '\n'
        requirements_path = os.path.join(repo_dir, 'requirements.txt')

        # Append missing packages to requirements file
        with open(requirements_path, "a") as f:
            f.write('\n' + missing_modules)

        # Retry running the tests if tries are left, else raise an error
        if tries > 0:
            return await run_python_tests(repo_dir, venv_name, tries)
        else:
            raise RuntimeError(f"Failed to add package: {missing_packages}")

    if code_errors:
        for error in code_errors:
            file_path = error['file']
            line_number = int(error['line'])
            error_message = f"Error in function {error['function']}"

            # Call OpenAI to fix the error
            await handle_code_error(file_path, line_number, error_message)

        # Retry running the tests if tries are left, else raise an error
        if tries > 0:
            return await run_python_tests(repo_dir, venv_name, tries - 1)
        else:
            raise RuntimeError("Failed to fix code errors")

    # You might want to handle the scenario where neither missing packages nor code errors exist
    return None


async def run_pytest_and_analyze(repo_dir, path_to_python_exec):
    """
    Runs pytest in the specified repository and analyzes the output for missing packages and code errors.

    :param repo_dir: Directory of the repository.
    :param path_to_python_exec: Path to the Python executable in the virtual environment.
    :return: A dictionary with lists of missing packages and code errors.
    """
    # Run pytest and capture output
    stdout, stderr = await cmd_popen(
        repo_dir=repo_dir,
        command_to_run=f"{path_to_python_exec} -m pytest -p no:cacheprovider --no-cov",
        shelled=True,
        sterr=True
    )
    # Define patterns to search for missing packages and code errors
    missing_package_pattern = re.compile(r'No module named (\S+)')
    code_error_pattern = re.compile(r'File "(.+)", line (\d+), in (\S+)')

    # Initialize result dictionary
    results = {
        'missing_packages': missing_package_pattern.findall(stdout.decode('utf-8')) if stdout else [],
        'code_errors': [
            {
                'file': match.group(1),
                'line': match.group(2),
                'function': match.group(3)
            }
            for match in code_error_pattern.finditer(stdout.decode('utf-8'))
        ] if stdout else []
    }
    unknown_packages = []
    missing_packages = []
    for package in results["missing_packages"]:
        package_name = package.replace("'","").replace('"', '')
        official_package_name = find_package_from_import(package_name)
        if official_package_name:
            missing_packages.append(package.replace("'","").replace('"', ''))
        else:
            unknown_packages.append(package_name)
    results['missing_packages'] = missing_packages
    results.update({"unknown_packages": unknown_packages})
    return results

def find_package_from_import(import_name):
    try:
        # Use importlib.metadata to get the distribution information
        distribution = importlib.metadata.distribution(import_name)
        return distribution.metadata["Name"]  # Extract the package name
    except Exception as exc:
        print(exc)
        return None


async def handle_code_error(file_path, line_number, error_message, context_lines=5):
    # Read the file content
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Get the lines around the error location
    start_line = max(line_number - context_lines - 1, 0)
    end_line = min(line_number + context_lines, len(lines))
    code_context = ''.join(lines[start_line:end_line])

    prompt = (
        f"There is an error in the following Python file:\n\n"
        f"File: {file_path}\n"
        f"Line: {line_number}\n"
        f"Error: {error_message}\n\n"
        f"Here is the code context:\n\n"
        f"{code_context}\n\n"
        f"Please provide a fix for this error."
    )

    response = customized_response(prompt)

    fix_suggestion = response.strip()

    # Apply the fix suggestion to the code (this step might need more context)
    with open(file_path, 'r') as file:
        lines = file.readlines()

    lines[line_number - 1] = fix_suggestion + '\n'

    with open(file_path, 'w') as file:
        file.writelines(lines)

    return fix_suggestion
