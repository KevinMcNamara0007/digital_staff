from src.utilities.general import file_filter
from src.utilities.git import clone_repo, check_current_branch, checkout_and_rebranch, repo_file_list, \
    show_file_contents
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
        return await produce_solution_service(user_prompt, file_list, repo_dir, new_branch_name, all_agent_responses, all_code, flow)
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
