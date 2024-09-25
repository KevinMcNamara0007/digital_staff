import json
import os
import shutil

import httpx
import requests
from dotenv import load_dotenv
from fastapi import HTTPException

# Load environment variables
env_file = f"config/{os.environ.get('ENV', '.env-dev')}"
load_dotenv(env_file)

# Retrieve environment variables
USER = os.environ["USER"]
USER_PASS = os.environ["USER_PASS"]
manifest_path = os.environ["manifest_path"]
llm_url = os.environ["llm_url"]
openai_key = os.environ["openai_key"]

# Load the manifest file
with open(manifest_path, "r") as manifest_file:
    manifest = json.load(manifest_file)

# Define agent roles
agent_roles = {
    "Manager": {"Background": "You are the Development Manager of a software team."},
    "Operations Agent": {"Background": "You are an Operations Agent."},
    "Software Developer": {"Background": "You are a Software Developer."},
    "Business Analyst": {"Background": "You are a Business Analyst."},
    "Content Agent": {"Background": "You are a Content Agent."},
    "Product Agent": {"Background": "You are a Product Agent."},
    "Code Tester": {"Background": "You are a Code Tester."}
}

# Define accepted file extensions
accepted_code_file_extensions = {
    '.cpp': 'C++', '.cc': 'C++', '.cp': 'C++', '.cxx': 'C++', '.h': 'C++',
    '.h++': 'C++', '.hh': 'C++', '.hpp': 'C++', '.hxx': 'C++', '.inc': 'C++',
    '.inl': 'C++', '.ipp': 'C++', '.tcc': 'C++', '.tpp': 'C++', '.cs': 'C#',
    '.cake': 'C#', '.cshtml': 'C#', '.csx': 'C#', '.c': 'C', '.cats': 'C',
    '.idc': 'C', '.w': 'C', '.java': 'Java', '.js': 'Javascript', '._js': 'Javascript',
    '.bones': 'Javascript', '.es': 'Javascript', '.es6': 'Javascript', '.frag': 'Javascript',
    '.gs': 'Javascript', '.jake': 'Javascript', '.jsb': 'Javascript', '.jscad': 'Javascript',
    '.jsfl': 'Javascript', '.jsm': 'Javascript', '.jss': 'Javascript', '.njs': 'Javascript',
    '.pac': 'Javascript', '.sjs': 'Javascript', '.ssjs': 'Javascript', '.sublime-build': 'Javascript',
    '.sublime-commands': 'Javascript', '.sublime-completions': 'Javascript', '.sublime-keymap': 'Javascript',
    '.sublime-macro': 'Javascript', '.sublime-menu': 'Javascript', '.sublime-mousemap': 'Javascript',
    '.sublime-project': 'Javascript', '.sublime-settings': 'Javascript', '.sublime-theme': 'Javascript',
    '.sublime-workspace': 'Javascript', '.sublime_metrics': 'Javascript', '.sublime_session': 'Javascript',
    '.xsjs': 'Javascript', '.xsjslib': 'Javascript', '.py': 'Python', '.bzl': 'Python',
    '.cgi': 'Python', '.fcgi': 'Python', '.gyp': 'Python', '.lmi': 'Python', '.pyde': 'Python',
    '.pyp': 'Python', '.pyt': 'Python', '.pyw': 'Python', '.rpy': 'Python', '.tac': 'Python',
    '.wsgi': 'Python', '.xpy': 'Python'
}

# Define excluded file types
exclude_file_types = [
    '__init__.py', 'cpython', '.h5', '.xml', '.doc', '.docx', '.dot', '.xml', '.db', '.sqlite', '.bmp',
    '.wav', '.jpg', '.zip', '.png', '.pdf', '.tar', '.csv', '.xls', '.xlsx', '.xlsm', '.xlt', '.xltx',
    '.ppt', '.pptx', '.txt', '.tsv', '.json', '.sql', ".log", ".tmp", ".bak", ".swp", ".DS_Store",
    ".pyc", ".pyo", "__pycache__/", ".pyd", ".class", ".jar", ".war", ".ear", ".iml", "node_modules/",
    ".o", ".obj", ".exe", ".dll", ".so", ".dylib", ".a", ".lib", ".out", ".pdb", ".mdb", ".gem",
    ".bundle/", ".config/", ".yardoc", "_yardoc/", ".rvmrc", ".xcodeproj", ".xcworkspace", ".xcuserdata",
    ".xcuserstate", "target/", ".rlib", ".tsbuildinfo", ".hi", ".bs", ".aux", ".bbl", ".blg", ".brf",
    ".idx", ".ilg", ".ind", ".lof", ".log", ".lot", ".nav", ".out", ".snm", ".toc", ".vrb", ".git/",
    ".svn/", ".hg/"
]

java_build_tools = {'pom.xml': 'Maven', 'build.gradle': 'Gradle'}


def file_filter(file_list):
    """
    Filters the list of files to include only accepted coding files, excluding __init__.py and empty files.

    :param file_list: List of file paths.
    :return: List of filtered file paths.
    """
    accepted_extensions = tuple(accepted_code_file_extensions.keys())
    return [
        file for file in file_list
        if file.endswith(accepted_extensions) and not any(excl in file for excl in exclude_file_types)
    ]


async def cleanup_cloned_repo(venv_name, repo_dir):
    """
    Remove all evidence of running tests on the repo to prevent adding files not recognized by the user.

    :param venv_name: Name of the virtual environment.
    :param repo_dir: Directory of the repository.
    :return: None
    """
    pytest_files = ['.pytest_cache', 'test.html', 'junit.xml', '.coverage']
    venv_path = os.path.join(repo_dir, venv_name)

    try:
        for file in pytest_files:
            file_path = os.path.join(repo_dir, file)
            if os.path.exists(file_path):
                os.remove(file_path)

        if os.path.exists(venv_path):
            shutil.rmtree(venv_path)
    except Exception as exc:
        error_message = f"Error during cleanup: {exc}"
        print(error_message)
        raise HTTPException(status_code=500, detail=error_message)


def check_token_count(string):
    """
    Checks the number of tokens in the given history string.

    :param history: History string.
    :return: Number of tokens.
    """
    return len(string)/4


async def delete_folder(repo_dir):
    try:
        shutil.rmtree(repo_dir)
    except Exception as exc:
        error_message = f"Error deleting folder: {exc}"
        print(error_message)
        raise HTTPException(status_code=500, detail=error_message)


async def stream_cpp_call(prompt, output_tokens=9000, url="http://192.168.1.13:8001/completion"):
    hermes = f"<|im_start|>system\n{prompt}<|im_end|>\n<|im_start|>user\n<|im_end|>\nassistant"
    llama = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>{prompt}<|start_header_id|>user<|end_header_id|><|eot_id|>assistant"

    try:
        response = requests.post(
            url,
            json={
                "prompt": llama,
                "stream": True,  # Enable streaming
                "n_predict": output_tokens,
                "temperature": 0.8,
                "stop": [
                    "</s>",
                    "<|end|>",
                    "<|eot_id|>",
                    "<|end_of_text|>",
                    "<|im_end|>",
                    "<|EOT|>",
                    "<|END_OF_TURN_TOKEN|>",
                    "<|end_of_turn|>",
                    "<|endoftext|>",
                    "assistant",
                    "user"
                ],
                "repeat_last_n": 0,
                "repeat_penalty": 1,
                "penalize_nl": False,
                "top_k": 0,
                "top_p": 1,
                "min_p": 0.05,
                "tfs_z": 1,
                "typical_p": 1,
                "presence_penalty": 0,
                "frequency_penalty": 0,
                "mirostat": 0,
                "mirostat_tau": 5,
                "mirostat_eta": 0.1,
                "grammar": "",
                "n_probs": 0,
                "min_keep": 0,
                "image_data": [],
                "cache_prompt": False,
                "api_key": ""
            },
            stream=True  # Enable streaming in the request
        )
        response.raise_for_status()

        # Stream content progressively
        for chunk in response.iter_lines():
            if chunk:
                yield chunk.decode('utf-8')

    except requests.RequestException as exc:
        raise HTTPException(status_code=500, detail=f"Failed to reach {url}\n{exc}")


async def stream_call_llm(prompt: str, output_tokens: int = 6000, extension: str = "/ask_a_pro_stream", url=llm_url):
    headers = {
        'token': 'fja0w3fj039jwiej092j0j-9ajw-3j-a9j-ea'
    }
    try:
        response = requests.post(
            llm_url + extension,
            json={
                "output_tokens": output_tokens,
                "prompt": prompt
            },
            headers=headers,
            stream=True  # Enable streaming in the request
        )
        response.raise_for_status()  # Raise an error for bad responses
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")  # Print the error
        return  # Handle the error as needed
    except Exception as err:
        print(f"An error occurred: {err}")
        return  # Handle the error as needed

    # Stream content progressively
    for chunk in response.iter_lines():
        if chunk:
            yield chunk.decode('utf-8')
