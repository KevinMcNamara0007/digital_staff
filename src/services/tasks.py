from src.utilities.git import clone_repo, check_current_branch, checkout_and_rebranch, repo_file_list
from src.utilities.inference import file_list_chunker, identify_relevant_files, refactor


async def repo_ops(user_prompt, https_clone_link, original_code_branch, new_branch_name):
    repo_dir = clone_repo(https_clone_link)
    cur_branch = check_current_branch(repo_dir)
    if cur_branch not in new_branch_name or new_branch_name not in cur_branch:
        _ = checkout_and_rebranch(new_branch_name, original_code_branch, repo_dir)
    file_list = repo_file_list(repo_dir)
    prompts = file_list_chunker(file_list, user_prompt)
    relevant_files = await identify_relevant_files(prompts)
    sanitized_relevant_files = [vetted_file for vetted_file in relevant_files if vetted_file in file_list]
    if len(sanitized_relevant_files) < 1:
        return "Clarifying question"
    return await refactor(user_prompt, sanitized_relevant_files, new_branch_name, repo_dir)
