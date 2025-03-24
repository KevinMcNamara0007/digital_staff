import asyncio
import base64
import json
import os
import shutil
from dotenv import load_dotenv
from fastapi import HTTPException
from openai import OpenAI
from openai.types.chat import ChatCompletionChunk

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


async def process_llm(prompt):
    try:
        response = await call_openai(prompt)
        finish_reason = response['finish_reason']
        llm_response = response['response']
        if 'stop' not in finish_reason:
            return await continue_response(prompt, llm_response)
        return llm_response
    except Exception as exc:
        print(f"Could not contact OpenAI: {exc}", flush=True)
        return None


async def continue_response(prompt, response):
    continue_rules = f"Please continue the response, use previous data as a source to continue from. Original Prompt: {prompt}"
    finish_reason = ''
    text = response
    tries = 0
    while 'stop' not in finish_reason.lower() and tries < 3:
        try:
            resp = await call_openai(str(text), continue_rules)
            finish_reason = resp['finish_reason']
            text = str(text) + str(resp['response'])
            tries = tries + 1
        except Exception as exc:
            print(f"Could not contact OAI: {exc}", flush=True)
            break
    return text


async def call_openai(prompt, model="gpt-4o"):
    client = OpenAI(api_key=openai_key)
    response = await asyncio.to_thread(client.chat.completions.create,
                                       model=model,
                                       messages=[{"role": "user", "content": prompt}])
    return response.choices[0].message.content


async def openai_stream(prompt, model="gpt-4o", image=None):
    client = OpenAI(api_key=openai_key)
    if image:
        base64_image = encode_image(image)
        messages = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                    },
                },
            ],
        }]
    else:
        messages = [{"role": "user", "content": prompt}]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        stream=True,

    )
    for chunk in response:
        try:
            # Access the content in the ChatCompletionChunk
            content = chunk.choices[0].delta.content
            if content:
                print("Yielding content:", content)
                yield content
        except AttributeError as e:
            print("Failed to parse chunk:", e)


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
    return len(string) / 4


async def delete_folder(repo_dir):
    try:
        shutil.rmtree(repo_dir)
    except Exception as exc:
        error_message = f"Error deleting folder: {exc}"
        print(error_message)
        raise HTTPException(status_code=500, detail=error_message)


def encode_image(image_bytes: bytes):
    return base64.b64encode(image_bytes).decode('utf-8')


async def image_to_text(prompt, image):
    base64_image = encode_image(image)
    client = OpenAI(api_key=openai_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    },
                ],
            }
        ],
        max_tokens=2000,
    )
    return response.choices[0].message.content
