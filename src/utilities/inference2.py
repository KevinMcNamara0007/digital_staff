import json

import requests
from fastapi import HTTPException
from openai import OpenAI

from src.utilities.general import manifest, llm_url, openai_key, check_token_count


def manager__development_agent_prompts(user_prompt, assets, software_type):
    return [
        f"You are an expert {software_type} developer. {user_prompt}, produce ONLY complete code for: {assets}.",
        # zero shot
        f"You are an expert {software_type} developer. {user_prompt}, produce ONLY complete code for: {assets}.",
        # one shot
        f"Review the following for accuracy and completness: {user_prompt}, produce ONLY complete code for: {assets}.",
        # checks for completeness
        f"Review the following for bugs and vulnerabilities and code smells: {user_prompt}, produce ONLY complete code for: {assets}.",
        # zero shot bugs and vulnerabilities and code smells
        f"Review the following for unit tests: {assets}. If there is none, create units tests. produce ONLY complete code.",
        # zero shot unit tests
        f"Add inline code comments for all key variables and methods, produce ONLY complete code for: {assets}.",
        # zero shot unit tests
        f"You are an expert {software_type}. Inspect and optimize code and unit test, correct where needed and produce complete code for: {assets}."
        # zero shot unit tests
    ]


async def agent_task(task, responses, code):
    print(f"Agent Task: {task}")
    print(f"Agent Response Token Amount: {check_token_count(responses)}")
    prompt = (f"Instructions:"
              f"1. This is your task: {task}."
              f"2. If your task requires a previous agents response, these are the previous agents responses: {responses}."
              f"3. If your task requires original code, use these files and their code as reference: {code}."
              f"4. RESPOND ONLY WITH FILE NAMES AND CODE.")
    print(f"Token Amount: {check_token_count(prompt)}")
    return customized_response(prompt)


async def produce_final_solution(user_prompt, file_list, agent_responses, original_code):
    prompt = (
            f"Instructions: "
            f"1. You are an elite coder assigned to complete the ask of this: {user_prompt} ."
            f"2. Your coding agents have helped you with certain tasks, use their answers as reference: [{agent_responses}]."
            f"3. This was the original code used to complete the agents tasks: [" + original_code.replace('"',
                                                                                                          "'") + "]."
                                                                                                                 f"4. These were the exact file names used {file_list}."
                                                                                                                 f"5. Using the responses of your agents and the original code, you will complete the users ask"
                                                                                                                 f"by producing a final code solution for each file and its code."
                                                                                                                 f"6. If your agents have created new files such as unit tests, please include those new files."
                                                                                                                 f"7. File code must only be code of type which is related with the extension of the file name."
                                                                                                                 f"8. YOU WILL ONLY RESPOND USING THIS JSON FORMAT EXAMPLE: "
                                                                                                                 '[{"FILE_NAME":"", "FILE_CODE":""},{"FILE_NAME":"", "FILE_CODE":""}]'
    )
    print(f"Final Solution Token Amount: {check_token_count(prompt)}")
    response = customized_response(prompt)
    response = response.replace('""', '')
    response = response.replace("```", '')
    response = response.replace('json', '')
    try:
        response = json.loads(response)
    except Exception as exc:
        print(f'Could not parse String Into JSON ERROR Will Remove all formatting: {exc}')
        response = response.replace('\n', '')
        response = response.replace('\\', '')
        try:
            response = json.loads(response)
        except Exception as exc:
            print("Removing Formatting Did not help final response, sending back regular string")
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


def customized_response(prompt):
    new_prompt = [{"role": "user", "content": prompt}]
    client = OpenAI(api_key=openai_key)
    response = client.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=new_prompt
    )
    content = response.choices[0].message.content
    return content
