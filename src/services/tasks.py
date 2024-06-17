import importlib
import os
import platform
import re
import shutil
import uuid
from importlib import metadata

import aiohttp

from src.utilities.general import file_filter, accepted_code_file_extensions
from src.utilities.git import clone_repo, check_current_branch, checkout_and_rebranch, repo_file_list, \
    show_file_contents, cmd_popen, cmd_run
from src.utilities.inference2 import manager__development_agent_prompts, agent_task, produce_final_solution, \
    customized_response, call_openai


async def get_repo_service(user_prompt, https_clone_link, original_code_branch, new_branch_name, flow="n"):
    repo_dir = await clone_repo(https_clone_link)
    cur_branch = await check_current_branch(repo_dir)
    if cur_branch not in new_branch_name or new_branch_name not in cur_branch:
        await checkout_and_rebranch(new_branch_name, original_code_branch, repo_dir)
    file_list = file_filter(await repo_file_list(repo_dir))
    # GET SPECIFIC FILES FROM LIST BASED ON USER_PROMPT
    prompt = (f"Instructions: 1. RESPOND WITH ONLY USING THE FILES NEEDED TO COMPLETE THE USER ASK: {user_prompt}."
              f"2. RESPOND ONLY IN FORMAT: filename1,filename2,filename3 ."
              f"3. THESE ARE THE FILES RELEVANT TO THE ASK: {await get_all_code(file_list, repo_dir, new_branch_name)}.")
    file_list = await call_openai(prompt)
    print(file_list)
    # API FLOW
    if flow == "y":
        await create_plan_service(user_prompt, file_list, repo_dir, new_branch_name, flow)
    return {"user_prompt": user_prompt, "files": file_list, "repo_dir": repo_dir}


async def create_plan_service(user_prompt, file_list, repo_dir, new_branch_name, flow="n"):
    if flow == "y":
        tasks = manager__development_agent_prompts(user_prompt, file_list)
        #API Get All Code Into 1 string
        all_code = await get_all_code(file_list, repo_dir, new_branch_name)
        #API Do Each Agent Task
        all_agent_responses = await process_agent_tasks(tasks, user_prompt, file_list, repo_dir, new_branch_name, all_code)
        return await produce_solution_service(user_prompt, file_list, repo_dir, new_branch_name, all_agent_responses, all_code, flow)
    #UI Get Software Type
    software_type = await get_software_type(file_list)
    print(f"SOFTWARE TYPE: {software_type}")
    #UI Return Manager Prompts
    return manager__development_agent_prompts(user_prompt, file_list, software_type)


async def process_agent_tasks(tasks, user_prompt, file_list, repo_dir, new_branch_name, all_code):
    all_agent_responses = ""
    for index, agent_prompt in enumerate(tasks):
        print(agent_prompt)
        agent_response = await agent_task_service(agent_prompt, user_prompt, file_list, repo_dir, new_branch_name, all_code, all_agent_responses, "y")
        all_agent_responses += f"{{Agent: {index}, Response: {agent_response}}}"
    return all_agent_responses


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
    return await customized_response(prompt)


async def produce_solution_service(user_prompt, file_list, repo_dir, new_branch_name, agent_responses, code="", flow="n"):
    if not code:
        code = await get_all_code(file_list, repo_dir, new_branch_name)
    return await produce_final_solution(user_prompt, file_list, agent_responses, code)


async def run_python_tests(repo_dir, present_venv_name=None, tries=3):
    """
    Runs the python tests if any are found otherwise just returns success message if the tests are ran or if no tests
    are found.
    :param repo_dir:
    :param present_venv_name:
    :param tries:
    :return:
    """
    unique_venv_name = present_venv_name or f"{uuid.uuid4().hex[:6].upper()}"

    # Create virtual environment
    await cmd_run(f"python -m venv {os.path.join(repo_dir, unique_venv_name)}")

    path_to_python_exec = os.path.join(unique_venv_name, 'Scripts',
                                       'python.exe') if platform.system() == "Windows" \
        else os.path.join(unique_venv_name,
                          'bin',
                          'python')
    # Ensure requirements.txt exists
    requirements_path = os.path.join(repo_dir, 'requirements.txt')
    if not os.path.exists(requirements_path):
        with open(requirements_path, 'w'):
            pass
    # Install dependencies
    await cmd_popen(repo_dir, f"{path_to_python_exec} -m pip install -r requirements.txt pytest pytest-cov httpx",
                    shelled=True)

    # Run tests and analyze results
    results = await run_pytest_and_analyze(repo_dir, path_to_python_exec)
    print(results)
    # Check for missing packages or code errors and attempt to fix them
    await failure_repair(results["missing_packages"], results["code_errors"], results["syntax_errors"],
                         results["general_errors"], repo_dir, unique_venv_name, tries)

    # If the tests pass, clean up
    await cleanup_post_test(unique_venv_name, repo_dir)

    return "Success"


async def run_pytest_and_analyze(repo_dir, path_to_python_exec):
    """
    Runs the pytest command and checks output for any errors, captures those errors and returns them as a dict
    :param repo_dir:
    :param path_to_python_exec:
    :return:
    """
    stdout, stderr = await cmd_popen(
        repo_dir=repo_dir,
        command_to_run=f"{path_to_python_exec} -m pytest -p no:cacheprovider --no-cov",
        sterr=True,
        shelled=True
    )
    output = stdout + stderr

    missing_packages, code_errors, syntax_errors, general_errors = parse_pytest_output(output)

    known_packages = []
    unknown_packages = []
    for package in missing_packages:
        official_package_name = find_package_from_import(package)
        if official_package_name:
            known_packages.append(package)
        else:
            unknown_packages.append(package)

    results = {
        'missing_packages': known_packages,
        'code_errors': code_errors,
        'syntax_errors': syntax_errors,
        'general_errors': general_errors,
        'unknown_packages': unknown_packages
    }

    return results


def parse_pytest_output(output):
    """
    Checks the pytest output for errors through pattern revision.
    :param output:
    :return:
    """
    missing_package_pattern = re.compile(r"No module named '(\S+)'")
    code_error_pattern = re.compile(r'File "(.+)", line (\d+), in (\S+)', re.MULTILINE)
    syntax_error_pattern = re.compile(r'SyntaxError: (.+)', re.MULTILINE)
    general_error_pattern = re.compile(r'ERROR (.+)', re.MULTILINE)
    traceback_pattern = re.compile(r'Traceback \(most recent call last\):(.+?)\n\n', re.DOTALL)

    missing_packages = missing_package_pattern.findall(output)
    code_errors = [
        {
            'file': match.group(1),
            'line': match.group(2),
            'function': match.group(3)
        }
        for match in code_error_pattern.finditer(output)
    ]

    syntax_errors = [
        {
            'file': match.group(1),
            'line': match.group(2),
            'message': match.group(3)
        }
        for match in code_error_pattern.finditer(output)
    ]

    general_errors = [
        {
            'error': general_error_match.group(1),
            'traceback': traceback_match.group(1).strip() if (
                traceback_match := traceback_pattern.search(output)) else None
        }
        for general_error_match in general_error_pattern.finditer(output)
    ]

    return missing_packages, code_errors, syntax_errors, general_errors


def find_package_from_import(import_name):
    """
    Attempts to identify a package by its import name.
    :param import_name:
    :return:
    """
    try:
        distribution = importlib.metadata.distribution(import_name)
        return distribution.metadata["Name"]
    except Exception as exc:
        print(exc)
        return None


async def failure_repair(missing_packages, code_errors, syntax_errors, general_errors, repo_dir, venv_name, tries=3):
    """
    Attempts to repair issues in code that were observed in the pytest output.
    :param missing_packages:
    :param code_errors:
    :param syntax_errors:
    :param general_errors:
    :param repo_dir:
    :param venv_name:
    :param tries:
    :return:
    """
    if missing_packages:
        validated_packages = []
        for package in missing_packages:
            is_valid = await validate_package(package)
            if is_valid:
                validated_packages.append(package)
            else:
                print(f"Package '{package}' is not valid or not found on PyPI.")
        if validated_packages:
            await update_requirements_file(repo_dir, validated_packages)
        return await retry_tests(repo_dir, venv_name, tries)

    if code_errors:
        for error in code_errors:
            file_path = error['file']
            line_number = int(error['line'])
            error_message = f"Error in function {error['function']}"
            await handle_code_error(file_path, line_number, error_message)
        return await retry_tests(repo_dir, venv_name, tries - 1)

    if syntax_errors:
        for error in syntax_errors:
            file_path = error['file']
            line_number = int(error['line'])
            error_message = f"Syntax error: {error['message']}"
            await handle_code_error(file_path, line_number, error_message)
        return await retry_tests(repo_dir, venv_name, tries - 1)

    if general_errors:
        for error in general_errors:
            print(f"General error detected: {error['error']}")
            if error.get('traceback'):
                print(f"Traceback: {error['traceback']}")
            # Handle specific known general errors
            await handle_general_error(error)
        return await retry_tests(repo_dir, venv_name, tries - 1)

    return None


async def validate_package(package):
    """
    Ensures the validity of the package names to avoid attempting to import non-existing packages from pypi.
    :param package:
    :return:
    """
    url = f"https://pypi.org/pypi/{package}/json"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return response.status == 200
    except Exception as e:
        print(f"Error validating package {package}: {e}")
        return False


async def update_requirements_file(repo_dir, packages):
    """
    Appends to the requirement's file.
    :param repo_dir:
    :param packages:
    :return:
    """
    requirements_path = os.path.join(repo_dir, 'requirements.txt')
    with open(requirements_path, "a") as f:
        f.write('\n' + '\n'.join(packages) + '\n')


async def retry_tests(repo_dir, venv_name, tries):
    """
    Retries running python tests for x number of tries.
    :param repo_dir:
    :param venv_name:
    :param tries:
    :return:
    """
    if tries > 0:
        return await run_python_tests(repo_dir, venv_name, tries)
    else:
        raise RuntimeError("Exceeded maximum retry attempts")


async def handle_code_error(file_path, line_number, error_message, context_lines=5):
    """
    Handles the code errors by attempting to change code line by line.
    :param file_path:
    :param line_number:
    :param error_message:
    :param context_lines:
    :return:
    """
    with open(file_path, 'r') as file:
        lines = file.readlines()

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

    lines[line_number - 1] = fix_suggestion + '\n'

    with open(file_path, 'w') as file:
        file.writelines(lines)

    return fix_suggestion


async def cleanup_post_test(venv_name, repo_dir):
    """
    Cleans up the venv and any pytest files.
    :param venv_name:
    :param repo_dir:
    :return:
    """
    venv_path = os.path.join(repo_dir, venv_name)
    if os.path.exists(venv_path):
        shutil.rmtree(venv_path)
    pytest_cache_dir = os.path.join(repo_dir, '.pytest_cache')
    if os.path.exists(pytest_cache_dir):
        shutil.rmtree(pytest_cache_dir)


async def check_code_language(code_changes):
    """
    Checks repo or incoming code for its language.
    :param code_changes:
    :return:
    """
    if len(code_changes.produced_code) < 1:
        file_list = await repo_file_list(code_changes.repo_dir)
        print(file_list)
        for file in file_list:
            for extension in accepted_code_file_extensions.keys():
                if file.endswith(extension):
                    return accepted_code_file_extensions[extension]
    for file in code_changes.produced_code:
        language = accepted_code_file_extensions.get(f'.{file.FILE_NAME.split(".")[-1]}')
        if language:
            return language
    return "N/A"


async def process_changes(final_artifact):
    """
    Decision engine to pass incoming changes to the right language framework.
    :param final_artifact:
    :return:
    """
    code_language = await check_code_language(final_artifact)
    if "N/A" in code_language:
        return "Unsupported language"
    await add_files_to_local_repo(final_artifact.produced_code, final_artifact.repo_dir)
    if code_language == "Python":
        return await run_python_tests(final_artifact.repo_dir)


async def add_files_to_local_repo(code_files, repo_dir):
    """
    Adds files to the cloned repo.
    :param code_files:
    :param repo_dir:
    :return:
    """
    for file in code_files:
        file_path = os.path.join(repo_dir, file.FILE_NAME)
        directory = os.path.dirname(file_path)

        # Ensure the directory exists
        os.makedirs(directory, exist_ok=True)

        # Write to the file
        with open(file_path, "w") as f:  # Use "w" to overwrite if the file exists
            f.write(file.FILE_CODE)


async def handle_general_error(error):
    """
    Handles general errors by analyzing and attempting to resolve known issues.
    :param error:
    :return:
    """
    error_message = error.get('error', '')
    traceback = error.get('traceback', '')

    if "FileNotFoundError" in error_message:
        missing_file_path = re.search(r"File '(.+)' not found", traceback)
        if missing_file_path:
            print(f"Missing file detected: {missing_file_path.group(1)}. Please ensure this file exists.")
            # Logic to handle missing file, e.g., create a dummy file or notify the user
            open(missing_file_path.group(1), 'w').close()  # Create an empty file as a placeholder
        else:
            print("File not found error, but no file path identified.")

    elif "PermissionError" in error_message:
        file_path = re.search(r"Permission denied: '(.+)'", traceback)
        if file_path:
            print(f"Permission error detected for file: {file_path.group(1)}. Please check file permissions.")
            # Logic to handle permission error, e.g., change file permissions
            os.chmod(file_path.group(1), 0o644)  # Change permissions to read/write for user
        else:
            print("Permission error, but no file path identified.")

    else:
        print(f"General error: {error_message}")
        if traceback:
            print(f"Traceback: {traceback}")
        # Additional logic to handle or report other types of general errors
