import json
import os
from dotenv import load_dotenv
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

accepted_code_file_extensions = [
    # C++
    '.cpp',
    '.cc',
    '.cp',
    '.cxx',
    '.h',
    '.h++',
    '.hh',
    '.hpp',
    '.hxx',
    '.inc',
    '.inl',
    '.ipp',
    '.tcc',
    '.tpp',
    # C#
    '.cs',
    '.cake',
    '.cshtml',
    '.csx',
    # C
    '.c',
    '.cats',
    '.h',
    '.idc',
    '.w',
    # Java
    '.java',
    # Javascript
    '.js',
    '._js',
    '.bones',
    '.es',
    '.es6',
    '.frag',
    '.gs',
    '.jake',
    '.jsb',
    '.jscad',
    '.jsfl',
    '.jsm',
    '.jss',
    '.njs',
    '.pac',
    '.sjs',
    '.ssjs',
    '.sublime-build',
    '.sublime-commands',
    '.sublime-completions',
    '.sublime-keymap',
    '.sublime-macro',
    '.sublime-menu',
    '.sublime-mousemap',
    '.sublime-project',
    '.sublime-settings',
    '.sublime-theme',
    '.sublime-workspace',
    '.sublime_metrics',
    '.sublime_session',
    '.xsjs',
    '.xsjslib',
    # Python
    '.py',
    '.bzl',
    '.cgi',
    '.fcgi',
    '.gyp',
    '.lmi',
    '.pyde',
    '.pyp',
    '.pyt',
    '.pyw',
    '.rpy',
    '.tac',
    '.wsgi',
    '.xpy'
]


def file_filter(file_list):
    """
    Takes a file list and returns a list of the files only of the files relating to coding files
    :param file_list:
    :return:
    """
    return [file for file in file_list if
            any(code_file_extension in file for code_file_extension in accepted_code_file_extensions)
            ]


def check_token_count(history):
    encoding = tiktoken.encoding_for_model("gpt-4-0125-preview")
    num_tokens = len(encoding.encode(history))
    return num_tokens
