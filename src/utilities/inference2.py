import json

import requests
from fastapi import HTTPException
from openai import OpenAI

from src.utilities.general import manifest, llm_url, openai_key, check_token_count


def manager__development_agent_prompts(user_prompt, assets, software_type):
    return [
        f"You are an expert {software_type} developer.  {user_prompt} using the following files: {assets}.", # zero shot
        f"You are an expert {software_type} developer.  {user_prompt} using the following files: {assets}.", # one shot
        f"review the following for accuracy and completness: {user_prompt} aginst the following {assets}.", # checks for completeness
        f"review the following for bugs and vulnerabilities and code smells: {user_prompt} aginst the following {assets}.", # zero shot bugs and vulnerabilities and code smells
        f"review the following for bugs and vulnerabilities and code smells: {user_prompt} aginst the following {assets}.", # one shot bugs and vulnerabilities and code smells
        f"review the following for unit tests: {user_prompt} aginst the following {assets}.", # zero shot unit tests
        f"You are an expert {software_type}.  Inspect and optimize code and unit test, look for faults and correct where needed: {assets}." # zero shot final check
    ]


async def agent_task(task, responses, code):
    print(f"Agent Task: {task}")
    print(f"Agent Response Token Amount: {check_token_count(responses)}")
    prompt = (f"Instructions:"
              f"1. This is your task: {task}."
              f"2. If there is nothing needed to be updated, please respond with: NA."
              f"3. If your task requires a previous agents response, these are the previous agents responses: {responses}."
              f"4. If your task requires original code, use these files and their code as reference: {code}.")
    print(f"Token Amount: {check_token_count(prompt)}")
    return customized_response(prompt)


async def produce_final_solution(user_prompt, file_list, agent_responses, original_code):
    prompt = (f"Instructions: 1. You are an elite coder assigned to complete the ask of this: {user_prompt} ."
              f"2. Your coding agents have helped you with certain tasks, use their answers as reference: [{agent_responses}]."
              "3. This was the original code used to complete the agents tasks: [" + original_code.replace('"', "'") + "]."
              f"4. These were the exact file names used {file_list}."
              f"5. Using the responses of your agents and the original code, you will complete the users ask"
              f"by producing a final code solution for each file and its code."
              "6. File code must only be code of type which is related with the extension of the file name."
              "7. YOU WILL ONLY RESPOND USING THIS JSON FORMAT EXAMPLE: "
              '[{"FILE_NAME":"", "FILE_CODE":""},{"FILE_NAME":"", "FILE_CODE":""}]'
              )
    print(f"Final Solution Token Amount: {check_token_count(prompt)}")
    response = customized_response(prompt)
    response = response.replace('""', '')
    response = response.replace("```", '')
    response = response.replace('json', '')
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


def customized_response(prompt):
    new_prompt = [{"role": "user", "content": prompt}]
    client = OpenAI(api_key=openai_key)
    response = client.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=new_prompt
    )
    content = response.choices[0].message.content
    return content