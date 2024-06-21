import subprocess


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