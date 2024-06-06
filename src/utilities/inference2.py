import json

import requests
from fastapi import HTTPException

from src.utilities.general import manifest, llm_url


def create_plan(user_prompt, file_list, repo_dir):
    manager_response = call_llm(
        prompt=f"Target Guidance: {user_prompt} \n Target Code: {file_list}",
        rules="You are a super intelligent Manager Agent capable of creating a development plan that assumes 10 "
              "developers where each developer is tasked sequentially and is able to handle a code pipeline that "
              "adjusts along the way to ensure a successful automatic development sprint. Please assume that you pass "
              "the request and target code to the first agent who then creates a feature, brand new code build, "
              "or correction. The first agent then send the code back to you and the n you send it to the second "
              "developer who is responsible to review and adjust the code based on the feature or guidance. The "
              "process continues sequentially where the code build is passed to the new developer. These are the "
              "developer roles from Devs 3 - 9: Dev 3, 4, and 5 do the same as Dev 2. Dev 6, 7, and 8 verify code for "
              "security. Dev 9 and 10 only write unit tests. Please ensure that the developer prompts that I can use "
              "for developers 1 - 10. Keys in JSON should be Developer Number, and Values should be the prompt. Please "
              "ensure each prompt is clear, concise and provides enough detail to pass to the next stage.\n"
              "EXAMPLE RESPONSE: { 'Developer2': 'Revise the code for bugs', 'Developer3': 'Revise Code for bugs' } "
    )
    print(manager_response)
    manager_manifest = json.loads(manager_response)
    return manager_manifest


def agent_task(task, responses, code):
    prompt = (f"Instructions: 1. You are an agent assigned to do this specific task: {task} ."
              f"2. If your task requires a previous agents response, use these as reference: [{responses}]."
              f"3. If you require code, use these files and their code as reference: [{code}]")
    return call_llm(prompt, "none")


def call_llm(prompt, rules="You are a Digital Assistant.", url=llm_url):
    try:
        response = requests.post(
            url,
            data={
                "prompt": '[{"role": "system", "content":' + rules + '}, {"role": "user", "content":' + prompt + '}]',
                "temperature": 0.05
            }
        )
        response = response.json()
        return response["choices"][0]["message"]["content"]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to reach {url}\n{exc}")