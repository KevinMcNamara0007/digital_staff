import json

import requests
from fastapi import HTTPException

from src.utilities.general import manifest, llm_url


async def create_plan(user_prompt, file_list, repo_dir):
    manager_response = call_llm(
        prompt=f"Target Guidance: {user_prompt} \n Target Code: {file_list}",
        rules="INSTRUCTIONS: "
              "1. You are AI Manager who creates a code development plan that has up to 10 developer agents if needed."
              "2. Each developer will have a sequential task based on the previous developer's task."
              "3. You will use the target guidance and target code files to assume what your developers will need to."
              "4. The last developer will always verify the code for security."
              '5. RESPOND ONLY IN THIS EXAMPLE FORMAT: { "Developer 2": "DEVELOPER TASK", "Developer 3": "DEVELOPER TASK"}.'
    )
    print(manager_response)
    manager_manifest = json.loads(manager_response)
    return manager_manifest


async def agent_task(task, responses, code):
    prompt = (f"Instructions: 1. You are an agent assigned to do this specific task: {task} ."
              f"2. If your task requires a previous agents response, use these as reference: [{responses}]."
              f"3. If you require code, use these files and their code as reference: [{code}]")
    return call_llm(prompt, "none")


async def produce_final_solution(user_prompt, file_list, agent_responses, original_code):
    prompt = (f"Instructions: 1. You are an elite coder assigned to complete the ask of this: {user_prompt} ."
              f"2. Your coding agents have helped you with certain tasks, use their answers as reference: [{agent_responses}]."
              "3. This was the original code used to complete the agents tasks: [" + original_code.replace('"', "'") + "]."
              f"4. These were the exact file names used {file_list}."
              f"5. Using the responses of your agents and the original code, you will complete the users ask"
              f"by producing a final code solution for each file and its code."
              "6. File code must only be code of type which is related with the extension of the file name."
              "7. YOU WILL RESPOND ONLY IN THIS JSON FORMAT EXAMPLE: "
              ' "File1": {"FILE_NAME":"", "FILE_CODE":""}, "File2" : {"FILE_NAME":"", "FILE_CODE":""}] .'
              )
    response = call_llm(prompt, "none")
    response = response.replace('""', '')
    # response = response.replace('\\n', '')
    # response = response.replace('\\', '')
    print(response)
    try:
        response = json.loads(response)
    except Exception as exc:
        print(f'Could not parse String Into JSON ERROR: {exc}')
    return response


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