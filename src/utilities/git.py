import asyncio
import os.path
import subprocess
from typing import Union

from fastapi import HTTPException
from src.utilities.general import USER, USER_PASS


async def clone_repo(repo_link):
    try:
        dest_folder = f'efs/repos/{repo_link.split("/")[-1].split(".git")[0]}'
        if not os.path.exists(dest_folder):
            output = subprocess.run(
                [
                    "git",
                    "clone",
                    f"https://{repo_link.replace('https://', '')}",
                    dest_folder
                ],
                capture_output=True
            )
            print(output.stdout)
        return dest_folder
    except Exception as exc:
        print(f"Could not clone repo: {exc}", flush=True)
        raise HTTPException(status_code=500, detail=f"Could not clone repo: {exc}")


async def check_current_branch(repo_dir):
    try:
        output = subprocess.Popen(
            "git branch --show-current".split(),
            cwd=f"./{repo_dir}",
            stdout=subprocess.PIPE
        )
        return output.communicate()[0].decode("utf-8").strip()
    except Exception as exc:
        print(f"Could not identify current branch: {exc}", flush=True)
        raise HTTPException(status_code=500, detail=f"Could not identify current branch: {exc}")


async def checkout_and_rebranch(new_branch_name, branch_to_fork_from, repo_dir):
    try:
        output = subprocess.Popen(
            f"git checkout -b {new_branch_name} origin/{branch_to_fork_from}".split(),
            cwd=f"./{repo_dir}",
            stdout=subprocess.PIPE
        )
        return output.communicate()[0].decode("utf-8")
    except Exception as exc:
        print(f"Could not fork from branch: {exc}")
        raise HTTPException(status_code=500, detail=f"Could not fork from branch: {exc}")


async def repo_file_list(repo_dir):
    try:
        output = subprocess.Popen(
            "git ls-tree -r HEAD --name-only".split(),
            cwd=f"./{repo_dir}",
            stdout=subprocess.PIPE
        )
        return output.communicate()[0].decode("utf-8").strip().split("\n")
    except Exception as exc:
        print(f"Could not get file list: {exc}", flush=True)
        raise HTTPException(status_code=500, detail=f"Could not get file list: {exc}")


async def show_file_contents(version, file_path, repo_dir):
    try:
        output = subprocess.Popen(
            f"git show {version}:{file_path}".split(),
            cwd=f"./{repo_dir}",
            stdout=subprocess.PIPE
        )
        return output.communicate()[0].decode("utf-8")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not read file: {exc}")


async def cmd_popen(repo_dir, command_to_run, shelled=False, tries=3, sterr=False):
    for _ in range(tries):
        try:
            process = subprocess.Popen(
                command_to_run.split(),
                cwd=f"./{repo_dir}",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE if sterr else subprocess.DEVNULL,
                shell=shelled
            )
            stdout, stderr = process.communicate()
            stdout = stdout.decode('utf-8') if stdout else ''
            stderr = stderr.decode('utf-8') if stderr else ''

            if process.returncode == 5 and "pytest" in command_to_run:
                return "No tests were found", ''
            if process.returncode == 3 or process.returncode == 4:
                raise RuntimeError(f"Command '{command_to_run}' failed with return code {process.returncode}: {stderr.strip()}")
            return stdout, stderr
        except subprocess.CalledProcessError as exc:
            print(f"CalledProcessError in subprocess: Command '{command_to_run}' failed with return code {exc.returncode}: {exc.stderr}")
            raise RuntimeError(f"Command '{command_to_run}' failed after multiple attempts: {exc}")
        except OSError as exc:
            print(f"OSError in subprocess: {exc}")
            if _ < tries - 1:
                continue
            raise RuntimeError(f"Command '{command_to_run}' failed after multiple attempts: {exc}")
        except Exception as exc:
            print(f"Error in subprocess: {exc}")
            if _ < tries - 1:
                continue
            raise RuntimeError(f"Command '{command_to_run}' failed after multiple attempts: {exc}")

    raise RuntimeError(f"Command '{command_to_run}' failed after {tries} attempts.")


async def cmd_run(command_to_run, tries=3):
    for _ in range(tries):
        try:
            command_output = subprocess.run(
                command_to_run.split(),
                capture_output=True,
                text=True,  # Python 3.7+ compatibility for decoding stdout
                check=True   # Raise subprocess.CalledProcessError for non-zero return codes
            )
            return command_output.stdout
        except subprocess.CalledProcessError as exc:
            print(f"Error in subprocess: {exc}")
            raise RuntimeError(f"Command '{command_to_run}' failed with return code {exc.returncode}: {exc.stderr}")
        except Exception as exc:
            print(f"Error in subprocess: {exc}")
            if _ < tries - 1:
                continue
            raise RuntimeError(f"Command '{command_to_run}' failed after multiple attempts: {exc}")
