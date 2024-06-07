from src.utilities.git import clone_repo, check_current_branch, checkout_and_rebranch, repo_file_list, \
    show_file_contents
from src.utilities.inference import file_list_chunker, identify_relevant_files, refactor
from src.utilities.inference2 import create_plan, agent_task


async def repo_ops(user_prompt, https_clone_link, original_code_branch, new_branch_name):
    repo_dir = await clone_repo(https_clone_link)
    cur_branch = await check_current_branch(repo_dir)
    if cur_branch not in new_branch_name or new_branch_name not in cur_branch:
        _ = await checkout_and_rebranch(new_branch_name, original_code_branch, repo_dir)
    file_list = await repo_file_list(repo_dir)
    prompts = await file_list_chunker(file_list, user_prompt)
    relevant_files = await identify_relevant_files(prompts)
    sanitized_relevant_files = [vetted_file for vetted_file in relevant_files if vetted_file in file_list]
    if len(sanitized_relevant_files) < 1:
        return "Clarifying question"
    return await refactor(user_prompt, sanitized_relevant_files, new_branch_name, repo_dir)


async def get_repo_service(user_prompt, https_clone_link, original_code_branch, new_branch_name, flow="n"):
    repo_dir = await clone_repo(https_clone_link)
    cur_branch = await check_current_branch(repo_dir)
    if cur_branch not in new_branch_name or new_branch_name not in cur_branch:
        _ = await checkout_and_rebranch(new_branch_name, original_code_branch, repo_dir)
    file_list = await repo_file_list(repo_dir)
    print(file_list)
    if flow == "y":
        await create_plan_service(user_prompt, file_list, repo_dir, new_branch_name, flow)
    return {"user_prompt": user_prompt, "files": file_list, "repo_dir": repo_dir}


async def create_plan_service(user_prompt, file_list, repo_dir, new_branch_name, flow="n"):
    if flow == "y":
        tasks = create_plan(user_prompt, file_list, repo_dir)
        # Get All Code Into 1 string
        all_code = await get_all_code(file_list, repo_dir, new_branch_name)
        # Do Each Agent Task
        all_agent_responses = ""
        for agent in tasks.keys():
            print(agent)
            agent_response = await agent_task_service(tasks[agent], user_prompt, file_list, repo_dir, new_branch_name,
                                                      all_code, all_agent_responses)
            all_agent_responses = all_agent_responses + f"[Agent: {agent}, Response: {agent_response}]:"
        return all_agent_responses
    return create_plan(user_prompt, file_list, repo_dir)


async def agent_task_service(task, user_prompt, file_list, repo_dir, new_branch_name, code="", response="", flow="n"):
    if flow == "y":
        response = agent_task(task, response, code)
        print(response)
        return response
    # Get All Code
    all_code = await get_all_code(file_list, repo_dir, new_branch_name)
    return agent_task(task, response, all_code)


async def get_all_code(file_list, repo_dir, new_branch_name):
    all_code = ""
    for file in file_list:
        file_code = await show_file_contents(new_branch_name, file, repo_dir)
        all_code = all_code + f"\n### *File Name: {file}* *File Code: {file_code}*###"
    return all_code
