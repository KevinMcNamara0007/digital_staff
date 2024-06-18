import asyncio
import json
import requests
from fastapi import HTTPException
from openai import OpenAI
from src.utilities.general import llm_url, openai_key, check_token_count

def manager_development_agent_prompts(user_prompt, assets, software_type):
    return [
        f"You are an expert {software_type} developer. {user_prompt}, produce ONLY complete code for: {assets}.",
        f"Review the following for accuracy and completeness: {user_prompt}, produce ONLY complete code for: {assets}.",
        f"Review the following for bugs and vulnerabilities and code smells: {user_prompt}, produce ONLY complete code for: {assets}.",
        f"Review the following for unit tests: {assets}. If there are none, create unit tests. Produce ONLY complete code.",
        f"Add inline code comments for all key variables and methods. Produce ONLY complete code for: {assets}.",
        f"You are an expert {software_type}. Inspect and optimize code and unit tests, correct where needed and produce complete code for: {assets}."
    ]

async def agent_task(task, responses, code):
    print(f"Agent Task: {task}")
    print(f"Agent Response Token Amount: {check_token_count(responses)}")
    prompt = (
        f"Instructions:\n"
        f"1. This is your task: {task}.\n"
        f"2. If your task requires a previous agent's response, these are the previous agents' responses: {responses}.\n"
        f"3. If your task requires original code, use these files and their code as reference: {code}.\n"
        f"4. RESPOND ONLY WITH FILE NAMES AND NEW OR UPDATED CODE."
    )
    print(f"Token Amount: {check_token_count(prompt)}")
    return await call_openai(prompt)

async def produce_final_solution(user_prompt, file_list, agent_responses, original_code):
    prompt = (
        "Instructions:\n"
        "1. You are an expert programmer.\n"
        "2. You will compile all agent code for each corresponding file and place it into a JSON format.\n"
        "3. You will only respond using this JSON format: [{'FILE_NAME':'file_name1', 'FILE_CODE':'file_code1'}, {'FILE_NAME':'file_name2', 'FILE_CODE':'file_code2'}].\n"
        f"4. File code will only be the code of the file associated with it.\n"
        f"5. These are the original file names: {file_list}.\n"
        f"6. Agents may have created new files such as unit test files. Please include new files into the JSON response as well.\n"
        f"7. Here are the agent responses you will reference: {agent_responses}\n"
        "8. Ensure that the JSON is correctly formatted and includes all file names and their corresponding code."
    )
    print(f"Final Solution Token Amount INPUT: {check_token_count(prompt)}")
    response = await call_openai(prompt, model="gpt-4-0125-preview")
    print(f"Final solution OUTPUT: {check_token_count(response)}")
    response = response.replace('""', '').replace("```", '').replace('json', '')

    try:
        response = json.loads(response)
    except json.JSONDecodeError as exc:
        print(f'Could not parse String Into JSON ERROR. Will Remove all formatting: {exc}')
        response = response.replace('\n', '').replace('\\', '')
        try:
            response = json.loads(response)
        except json.JSONDecodeError:
            print("Removing Formatting Did not help final response, sending back regular string")
    return response

async def call_openai(prompt, model="gpt-4o"):
    client = OpenAI(api_key=openai_key)
    response = await asyncio.to_thread(client.chat.completions.create,
                                       model=model,
                                       messages=[{"role": "user", "content": prompt}])
    return response.choices[0].message.content

def call_llm(prompt, rules="You are a Digital Assistant.", url=llm_url):
    try:
        response = requests.post(
            url,
            json={
                "prompt": [{"role": "system", "content": rules}, {"role": "user", "content": prompt}],
                "temperature": 0.05
            }
        )
        response.raise_for_status()  # Ensure we raise an error for bad responses
        return response.json()["choices"][0]["message"]["content"]
    except requests.RequestException as exc:
        raise HTTPException(status_code=500, detail=f"Failed to reach {url}\n{exc}")

async def customized_response(prompt):
    return await call_openai(prompt, model="gpt-4o")
