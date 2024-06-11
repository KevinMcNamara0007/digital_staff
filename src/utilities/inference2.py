import json

import requests
from fastapi import HTTPException
from openai import OpenAI

from src.utilities.general import manifest, llm_url, openai_key


def manager__development_agent_prompts(user_prompt, file_list):
    return [
        f'You are a software engineer. You are asked to complete the ask of {user_prompt} using the following files: {file_list}.',
        f'You are a software engineer. You will review agent 1 code and certify that agent 1 fulfilled the ask of: {user_prompt}. If the ask is not completed, complete the ask.',
        f'You are a software engineer. You will review agent 1 and agent 2 code. Certify that both agents fulfilled the ask of: {user_prompt}. If the ask is not completed, complete the ask.',
        f'You are a software engineer. You will fix all major bugs, vulnerabilities and code smells from agent 1, 2, and 3.',
        f'You are software engineer who specializes in security. You will review and update agent code for security if needed.',
        f'You are a software engineer who specializes in code testing. If there is unit test code please update the code. If there is no unit test code please create unit tests for following files {file_list} and agent code.',
        f'You are a software engineer who specializes in reviewing code. Inspect all agent code and unit test code from agents for faults and fix where needed.'
    ]


async def agent_task(task, responses, code):
    prompt = (f"Instructions:"
              f"1. This is your task: {task}."
              f"2. You will ONLY RESPOND with the updated code."
              f"3. You will not provide any explanation to any of the code."
              f"4. If there is nothing needed to be updated, please respond with: NA."
              f"2. If your task requires a previous agents response, these are the previous agents responses: {responses}."
              f"3. If your task requires original code, use these files and their code as reference: {code}.")
    return call_llm(prompt, "none")


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