import json
import os
import shutil
from dotenv import load_dotenv
from fastapi import HTTPException
import tiktoken

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

async def cleanup_post_test(venv_name, repo_dir):
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

def check_token_count(history):
    """
    Checks the number of tokens in the given history string.

    :param history: History string.
    :return: Number of tokens.
    """
    encoding = tiktoken.encoding_for_model("gpt-4-0125-preview")
    return len(encoding.encode(history))
