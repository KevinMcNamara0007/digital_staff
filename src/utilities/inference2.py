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
        f"Review the following for accuracy and completeness: {user_prompt}, produce ONLY complete code for: {assets}.",
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
              f"4. RESPOND ONLY WITH FILE NAMES AND NEW OR UPDATED CODE.")
    print(f"Token Amount: {check_token_count(prompt)}")
    return customized_response(prompt)


async def produce_final_solution(user_prompt, file_list, agent_responses, original_code):
    prompt = (
        "Instructions:"
        "1. You are an expert programmer."
        "2. You will compile all agent code for each corresponding file and place it into a JSON format."
        "3. You will only respond using this JSON format: [{\"FILE_NAME\":\"file_name1\", \"FILE_CODE\":\"file_code1\"}, {\"FILE_NAME\":\"file_name2\", \"FILE_CODE\":\"file_code2\"}]."
        "4. File code will only be the code of the file associated with it."
        f"5. These are the original file names: {file_list}."
        "6. Agents may have created new files. Please include new files into the JSON response as well."
        f"7. Here are the agent responses you will reference: {agent_responses}"
        "8. Ensure that the JSON is correctly formatted and includes all file names and their corresponding code."
    )
    print(f"Final Solution Token Amount INPUT: {check_token_count(prompt)}")
    response = call_turbo(prompt)
    print(f"Final solution OUTPUT: {check_token_count(response)}")
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
        model="gpt-4o",
        messages=new_prompt
    )
    content = response.choices[0].message.content
    return content


def call_turbo(prompt):
    new_prompt = [{"role": "user", "content": prompt}]
    client = OpenAI(api_key=openai_key)
    response = client.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=new_prompt
    )
    content = response.choices[0].message.content
    return content