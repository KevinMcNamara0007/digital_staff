import json
import os
import shutil

from dotenv import load_dotenv
from fastapi import HTTPException
import tiktoken

if os.environ.get("ENV"):
    load_dotenv(f"config/{os.environ['ENV']}")
else:
    load_dotenv("config/.env-dev")

USER = os.environ["USER"]
USER_PASS = os.environ["USER_PASS"]
manifest_path = os.environ["manifest_path"]
llm_url = os.environ["llm_url"]
openai_key = os.environ["openai_key"]

with open(manifest_path, "r") as manifest_file:
    manifest = json.load(manifest_file)

agent_roles = {
    "Manager": {
        "Background": "You are the Development Manager of a software team."
    },
    "Operations Agent": {
        "Background": "You are an Operations Agent.",
    },
    "Software Developer": {
        "Background": "You are a Software Developer.",
    },
    "Business Analyst": {
        "Background": "You are a Business Analyst.",
    },
    "Content Agent": {
        "Background": "You are a Content Agent.",
    },
    "Product Agent": {
        "Background": "You are a Product Agent.",
    },
    "Code Tester": {
        "Background": "You are a Code Tester."
    }
}

accepted_code_file_extensions = {
    # '.cpp': 'C++',
    # '.cc': 'C++',
    # '.cp': 'C++',
    # '.cxx': 'C++',
    # '.h': 'C++',
    # '.h++': 'C++',
    # '.hh': 'C++',
    # '.hpp': 'C++',
    # '.hxx': 'C++',
    # '.inc': 'C++',
    # '.inl': 'C++',
    # '.ipp': 'C++',
    # '.tcc': 'C++',
    # '.tpp': 'C++',
    # '.cs': 'C#',
    # '.cake': 'C#',
    # '.cshtml': 'C#',
    # '.csx': 'C#',
    # '.c': 'C',
    # '.cats': 'C',
    # '.idc': 'C',
    # '.w': 'C',
    # '.java': 'Java',
    # '.js': 'Javascript',
    # '._js': 'Javascript',
    # '.bones': 'Javascript',
    # '.es': 'Javascript',
    # '.es6': 'Javascript',
    # '.frag': 'Javascript',
    # '.gs': 'Javascript',
    # '.jake': 'Javascript',
    # '.jsb': 'Javascript',
    # '.jscad': 'Javascript',
    # '.jsfl': 'Javascript',
    # '.jsm': 'Javascript',
    # '.jss': 'Javascript',
    # '.njs': 'Javascript',
    # '.pac': 'Javascript',
    # '.sjs': 'Javascript',
    # '.ssjs': 'Javascript',
    # '.sublime-build': 'Javascript',
    # '.sublime-commands': 'Javascript',
    # '.sublime-completions': 'Javascript',
    # '.sublime-keymap': 'Javascript',
    # '.sublime-macro': 'Javascript',
    # '.sublime-menu': 'Javascript',
    # '.sublime-mousemap': 'Javascript',
    # '.sublime-project': 'Javascript',
    # '.sublime-settings': 'Javascript',
    # '.sublime-theme': 'Javascript',
    # '.sublime-workspace': 'Javascript',
    # '.sublime_metrics': 'Javascript',
    # '.sublime_session': 'Javascript',
    # '.xsjs': 'Javascript',
    # '.xsjslib': 'Javascript',
    '.py': 'Python',
    '.bzl': 'Python',
    '.cgi': 'Python',
    '.fcgi': 'Python',
    '.gyp': 'Python',
    '.lmi': 'Python',
    '.pyde': 'Python',
    '.pyp': 'Python',
    '.pyt': 'Python',
    '.pyw': 'Python',
    '.rpy': 'Python',
    '.tac': 'Python',
    '.wsgi': 'Python',
    '.xpy': 'Python',
}


def file_filter(file_list):
    """
    Takes a file list and returns a list of the files only of the files relating to accepted coding files
    :param file_list:
    :return:
    """
    return [file for file in file_list if
            any(code_file_extension in file for code_file_extension in accepted_code_file_extensions.keys())
            ]


async def cleanup_post_test(venv_name, repo_dir):
    """
    Remove all evidence of running tests on the repo, to prevent adding files not recognized by the user.
    :param venv_name:
    :param repo_dir:
    :return:
    """
    pytest_files = ['.pytest_cache', 'test.html', 'junit.xml', '.coverage']
    venv_path = f"{repo_dir}\\{venv_name}"
    try:
        for file in pytest_files:
            pytest_file_path = f"{repo_dir}\\{file}"
            if os.path.exists(pytest_file_path):
                os.remove(pytest_file_path)
        if os.path.exists(venv_path):
            shutil.rmtree(venv_path)
    except Exception as exc:
        print(f"Error at cleanup: {exc}")
        raise HTTPException(status_code=500, detail=f"Error at cleanup: {exc}")



def check_token_count(history):
    encoding = tiktoken.encoding_for_model("gpt-4-0125-preview")
    num_tokens = len(encoding.encode(history))
    return num_tokens
