import os
import asyncio
from concurrent.futures import ThreadPoolExecutor
import platform
import re
import uuid
from importlib import metadata
import aiohttp
from src.utilities.general import file_filter, accepted_code_file_extensions, cleanup_cloned_repo, check_token_count
from src.utilities.git import (
    clone_repo,
    check_current_branch,
    checkout_and_rebranch,
    repo_file_list,
    show_file_contents, show_repo_changes
)
from src.utilities.cli import cmd_popen, cmd_run
from src.utilities.inference2 import (
    manager_development_agent_prompts,
    agent_task,
    produce_final_solution,
    customized_response, call_openai, compile_agent_code, produce_final_solution_for_large_repo, call_llm,
)


async def get_repo_service(user_prompt, https_clone_link, original_code_branch, new_branch_name, flow="n"):
    repo_dir = await clone_repo(https_clone_link)
    cur_branch = await check_current_branch(repo_dir)
    if cur_branch != new_branch_name.strip():
        await checkout_and_rebranch(new_branch_name, original_code_branch, repo_dir)
    file_list = file_filter(await repo_file_list(repo_dir))
    # GET SPECIFIC FILES FROM LIST BASED ON USER_PROMPT
    required_files = []
    for file in file_list:
        file_code = await get_code(file, repo_dir, new_branch_name)
        prompt = ("You are a expert programming assistant who will only respond with 'yes' or 'no' based on the users ask."
                  "You will say 'yes' to a file if it can be modified or adjusted to fulfil the users ask."
                  "Respond with either 'YES' OR 'NO' only."
                  f"This is the user's request: {user_prompt}."
                  f"This is the user's file code: {file_code}")
        response = await call_llm(prompt, 100)
        print(f"File: {file} , needed: {response}")
        if 'YES' in response.upper():
            required_files.append(file)
    # API FLOW
    if flow == "y":
        return await create_plan_service(user_prompt, required_files, repo_dir, new_branch_name, flow)
    return {"user_prompt": user_prompt, "files": required_files, "repo_dir": repo_dir}


async def create_plan_service(user_prompt, file_list, repo_dir, new_branch_name, flow="n"):
    if flow == "y":
        tasks = manager_development_agent_prompts(user_prompt, file_list)
        all_code = await get_all_code(file_list, repo_dir, new_branch_name)
        all_agent_responses = await process_agent_tasks(tasks, user_prompt, file_list, repo_dir, new_branch_name,
                                                        all_code)
        return await produce_solution_service(user_prompt, file_list, repo_dir, new_branch_name, all_agent_responses,
                                              all_code, flow)
    software_type = await get_software_type(file_list)
    return manager_development_agent_prompts(user_prompt, file_list, software_type)


async def process_agent_tasks(tasks, user_prompt, file_list, repo_dir, new_branch_name, all_code):
    tasks_responses = await asyncio.gather(
        *[
            agent_task_service(agent_prompt, user_prompt, file_list, repo_dir, new_branch_name, all_code)
            for agent_prompt in tasks
        ]
    )
    all_agent_responses = "".join(
        [f"{{Agent: {i}, Response: {response}}}" for i, response in enumerate(tasks_responses)])
    return all_agent_responses


async def agent_task_service(task, user_prompt, file_list, repo_dir, new_branch_name, code="", response="", flow="n"):
    if flow == "y":
        return await agent_task(task, response, code)
    all_code = await get_all_code(file_list, repo_dir, new_branch_name)
    print(f"Total Code Token Count: {check_token_count(all_code)}")

    compiled_code = await agent_task(task, response, all_code)
    return {"agent_response": compiled_code}

async def process_file(task, file, repo_dir, new_branch_name, response):
    file_code = await get_code(file, repo_dir, new_branch_name)
    compiled_code = await agent_task(task, response, file_code)
    print(f"File: {file}  completed.")
    return {"FILE_NAME": file, "FILE_CODE": compiled_code}


async def agent_task_per_file(task, user_prompt, file_list, repo_dir, new_branch_name, code="", response="", flow="n"):
    tasks = [
        process_file(task, file, repo_dir, new_branch_name, response)
        for file in file_list
    ]
    file_code_list = await asyncio.gather(*tasks)
    return {"agent_response_list": file_code_list}


async def get_code(file, repo_dir, new_branch_name):
    code = await show_file_contents(new_branch_name, file, repo_dir)
    return f"### *File Name: {file}* *File Code: {code}*###"


async def get_all_code(file_list, repo_dir, new_branch_name):
    tasks = [show_file_contents(new_branch_name, file, repo_dir) for file in file_list]
    files_code = await asyncio.gather(*tasks)
    return "\n".join([f"### *File Name: {file}* *File Code: {code}*###" for file, code in zip(file_list, files_code)])


async def get_software_type(assets):
    prompt = f"Respond only with the type of developer that made these files {assets}"
    return await call_openai(prompt)


async def produce_solution_service(user_prompt, file_list, repo_dir, new_branch_name, agent_responses, code="", flow="n"):
    if not code:
        code = await get_all_code(file_list, repo_dir, new_branch_name)
        # if check_token_count(code) > 2000:
        #     return await produce_final_solution_for_large_repo(user_prompt, file_list, agent_responses, code)
    return await produce_final_solution(user_prompt, file_list, agent_responses, code)


async def run_python_tests(repo_dir, present_venv_name=None, tries=3):
    unique_venv_name = present_venv_name or f"{uuid.uuid4().hex[:6].upper()}"
    await cmd_run(f"python -m venv {os.path.join(repo_dir, unique_venv_name)}")
    path_to_python_exec = (
        os.path.join(unique_venv_name, 'Scripts', 'python.exe')
        if platform.system() == "Windows"
        else os.path.join(unique_venv_name, 'bin', 'python')
    )
    requirements_path = os.path.join(repo_dir, 'requirements.txt')
    if not os.path.exists(requirements_path):
        with open(requirements_path, 'w'):
            pass
    await cmd_popen(repo_dir, f"{path_to_python_exec} -m pip install -r requirements.txt pytest pytest-cov httpx",
                    shelled=True)
    results = await run_pytest_and_analyze(repo_dir, path_to_python_exec)
    print(results)
    # Check for missing packages or code errors and attempt to fix them
    await failure_repair(results["missing_packages"], results["code_errors"], results["general_errors"], repo_dir,
                         unique_venv_name, tries)

    # If the tests pass, clean up
    await cleanup_cloned_repo(unique_venv_name, repo_dir)
    return "Success"


async def run_pytest_and_analyze(repo_dir, path_to_python_exec):
    stdout, stderr = await cmd_popen(repo_dir, f"{path_to_python_exec} -m pytest -p no:cacheprovider --no-cov",
                                     sterr=True, shelled=True)
    output = stdout + stderr

    missing_packages, code_errors, general_errors = parse_pytest_output(output)

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
        'general_errors': general_errors,
        'unknown_packages': unknown_packages,
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

    general_errors = [
        {
            'error': general_error_match.group(1),
            'traceback': traceback_match.group(1).strip() if (
                traceback_match := traceback_pattern.search(output)) else None
        }
        for general_error_match in general_error_pattern.finditer(output)
    ]

    return missing_packages, code_errors, general_errors


def find_package_from_import(import_name):
    try:
        distribution = metadata.distribution(import_name)
        return distribution.metadata["Name"]
    except Exception:
        return None


async def failure_repair(missing_packages, code_errors, general_errors, repo_dir, venv_name, tries=3):
    """
    Attempts to repair issues in code that were observed in the pytest output.
    :param missing_packages:
    :param code_errors:
    :param general_errors:
    :param repo_dir:
    :param venv_name:
    :param tries:
    :return:
    """
    if missing_packages:
        validated_packages = [pkg for pkg in missing_packages if await validate_package(pkg)]
        if validated_packages:
            await update_requirements_file(repo_dir, validated_packages)
        return await retry_tests(repo_dir, venv_name, tries)
    if code_errors:
        await handle_code_errors(code_errors)
        return await retry_tests(repo_dir, venv_name, tries - 1)

    if general_errors:
        await handle_general_errors(general_errors)
        return await retry_tests(repo_dir, venv_name, tries - 1)
    return None


async def validate_package(package):
    url = f"https://pypi.org/pypi/{package}/json"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                return response.status == 200
    except Exception:
        return False


async def update_requirements_file(repo_dir, packages):
    requirements_path = os.path.join(repo_dir, 'requirements.txt')
    with open(requirements_path, "a") as f:
        f.write('\n'.join(packages) + '\n')


async def retry_tests(repo_dir, venv_name, tries):
    if tries > 0:
        return await run_python_tests(repo_dir, venv_name, tries)
    raise RuntimeError("Exceeded maximum retry attempts")


async def handle_code_errors(errors):
    for error in errors:
        file_path, line_number, error_message = error['file'], int(
            error['line']), f"Error in function {error['function']}"
        await handle_code_error(file_path, line_number, error_message)


async def handle_code_error(file_path, line_number, error_message, context_lines=5):
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
    fix_suggestion = (await customized_response(prompt)).strip()
    lines[line_number - 1] = fix_suggestion + '\n'
    with open(file_path, 'w') as file:
        file.writelines(lines)
    return fix_suggestion


async def handle_general_errors(errors):
    for error in errors:
        error_message, traceback = error['error'], error.get('traceback', '')
        if "FileNotFoundError" in error_message:
            missing_file_path = re.search(r"File '(.+)' not found", traceback)
            if missing_file_path:
                open(missing_file_path.group(1), 'w').close()
        elif "PermissionError" in error_message:
            file_path = re.search(r"Permission denied: '(.+)'", traceback)
            if file_path:
                os.chmod(file_path.group(1), 0o644)
        else:
            print(f"General error: {error_message}")
            if traceback:
                print(f"Traceback: {traceback}")


async def check_code_language(code_changes):
    if not code_changes.produced_code:
        file_list = await repo_file_list(code_changes.repo_dir)
        for file in file_list:
            if any(file.endswith(ext) for ext in accepted_code_file_extensions.keys()):
                return accepted_code_file_extensions[os.path.splitext(file)[1]]
    for file in code_changes.produced_code:
        language = accepted_code_file_extensions.get(f'.{file.FILE_NAME.split(".")[-1]}')
        if language:
            return language
    return "N/A"


async def process_changes(final_artifact):
    code_language = await check_code_language(final_artifact)
    if "N/A" in code_language:
        return "Unsupported language"
    await add_files_to_local_repo(final_artifact.produced_code, final_artifact.repo_dir)
    if code_language == "Python":
        return await run_python_tests(final_artifact.repo_dir)


async def add_files_to_local_repo(code_files, repo_dir):
    for file in code_files:
        file_path = os.path.join(repo_dir, file.FILE_NAME)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write(file.FILE_CODE)


async def show_all_changes(final_artifact):
    await add_files_to_local_repo(final_artifact.produced_code, final_artifact.repo_dir)
    changes = await show_repo_changes(final_artifact.repo_dir)
    clean_changes = re.sub(r'\x1b\[.*?m', '', changes)
    files = clean_changes.split('No newline at end of file')
    html_output = ''
    print(files)
    for file in files:
        lines = file.split("\n")
        for line in lines:
            if "diff --git" in line:
                html_output += f''
            elif "index" in line:
                html_output += f''
            elif "No newline at end of file" in line:
                html_output += f''
            elif "---" in line:
                html_output += f'<div class="diff-file-right">{line}</div>\n'
            elif "+++" in line:
                html_output += f'<div class="diff-file-left">{line}</div>\n'
            elif "@@" in line:
                html_output += f'<div class="diff-hunk">{line}</div>\n'
            elif line.startswith('+') and not line.startswith('+++'):
                html_output += f'<span class="diff-added right">{line}</span>\n'
            elif line.startswith('-') and not line.startswith('---'):
                html_output += f'<span class="diff-removed left">{line}</span>\n'
            else:
                html_output += f'<div>{line}</div>\n'
    return html_output


async def git_add_commit_push(repo_dir, commit_message, branch='main', remote='origin'):
    """
    Adds, commits, and pushes changes to a cloned repository.

    :param repo_dir: Directory of the cloned repository.
    :param commit_message: Commit message for the changes.
    :param branch: Branch to push the changes to (default is 'main').
    :param remote: Remote to push the changes to (default is 'origin').
    """
    results = {}
    try:
        # Ensure the repository directory exists
        if not os.path.isdir(repo_dir):
            raise RuntimeError(f"Repository directory '{repo_dir}' does not exist.")

        # Ensure that the repo_dir is an absolute path
        repo_dir = os.path.abspath(repo_dir)

        # Step 1: Check git status before running add command
        stdout = await cmd_run(f"git -C {repo_dir} status", tries=3)
        results['status'] = {'stdout': stdout, 'stderr': ''}
        print("Git status checked.")

        # Step 2: Add files to the staging area, forcing addition of ignored files
        stdout = await cmd_run(f"git -C {repo_dir} add -f .", tries=3)
        results['add'] = {'stdout': stdout, 'stderr': ''}
        print("Files added to the staging area.")

        # Step 3: Commit the changes
        stdout = await cmd_run(f'git -C {repo_dir} commit -m', tries=3, opts=f'"{commit_message}"')
        results['commit'] = {'stdout': stdout, 'stderr': ''}
        print("Changes committed.")

        # Step 4: Push the changes
        stdout = await cmd_run(f'git -C {repo_dir} push {remote} {branch}', tries=3)
        results['push'] = {'stdout': stdout, 'stderr': ''}
        print("Changes pushed to the remote repository.")
    except RuntimeError as e:
        print(f"Error during git operations: {e}")
        results['error'] = str(e)

    return results
