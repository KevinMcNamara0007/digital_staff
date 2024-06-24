import os.path
from src.utilities.cli import cmd_popen, cmd_run


async def clone_repo(repo_link):
    dest_folder = f'efs/repos/{repo_link.split("/")[-1].split(".git")[0]}'
    if not os.path.exists(dest_folder):
        output = await cmd_run(
            command_to_run=f"git clone https://{repo_link.replace('https://', '')} {dest_folder}"
        )
        return output


async def check_current_branch(repo_dir):
    stdout, stderr = await cmd_popen(
        repo_dir=repo_dir,
        command_to_run="git branch --show-current"
    )
    if stderr:
        raise RuntimeError(str(stderr))
    return stdout or stderr


async def checkout_and_rebranch(new_branch_name, branch_to_fork_from, repo_dir):
    stdout, stderr = await cmd_popen(
        repo_dir=repo_dir,
        command_to_run=f"git checkout -b {new_branch_name} origin/{branch_to_fork_from}"
    )
    return stdout or stderr


async def repo_file_list(repo_dir):
    stdout, stderr = await cmd_popen(
        repo_dir=repo_dir,
        command_to_run="git ls-tree -r HEAD --name-only"
    )
    if stderr:
        raise RuntimeError(str(stderr))
    return stdout or stderr


async def show_file_contents(version, file_path, repo_dir):
    stdout, stderr = await cmd_popen(
        repo_dir=repo_dir,
        command_to_run=f"git show {version}:{file_path}"
    )
    return stdout or stderr


async def show_repo_changes(repo_dir):
    stdout, stderr = await cmd_popen(
        repo_dir=repo_dir,
        command_to_run="git diff --color-words"
    )
    return stdout or stderr


async def check_git_status(repo_dir):
    stdout, stderr = await cmd_popen(
        repo_dir=repo_dir,
        command_to_run="git status",
        shelled=True,
        stderr=True
    )
    return stdout or stderr


async def add_changes_to_branch(repo_dir):
    stdout, stderr = await cmd_popen(
        repo_dir=repo_dir,
        command_to_run="git add .",
        shelled=True,
        stderr=True
    )
    return stdout or stderr


async def commit_repo_changes(repo_dir, message="Auto repo updates"):
    stdout, stderr = await cmd_popen(
        repo_dir=repo_dir,
        command_to_run=f"git commit -m {message}",
        shelled=True,
        stderr=True
    )
    return stdout or stderr


async def push_changes_to_repo(repo_dir):
    stdout, stderr = await cmd_popen(
        repo_dir=repo_dir,
        command_to_run="git push",
        shelled=True,
        stderr=True
    )
    return stdout or stderr
