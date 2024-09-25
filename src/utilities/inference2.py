import asyncio
import base64
import json
import time

import requests
from fastapi import HTTPException
from openai import OpenAI


from src.utilities.general import llm_url, openai_key, check_token_count, stream_cpp_call, stream_call_llm
import re


def manager_development_agent_prompts(user_prompt, assets, software_type):
    return [
        f"You are an expert {software_type} developer. {user_prompt}, produce ONLY complete code.",
        f"Review the following code for accuracy and completeness and add inline code comments, produce and return ONLY complete code.",
        f"correct the following code for bugs and vulnerabilities. produce and return ONLY complete code.",
        f"You are an expert {software_type}. Inspect and optimize code, correct where needed and produce complete code."
    ]


async def agent_task(task, responses, code, model="oai"):
    print(f"Agent Task: {task}")
    prompt = (
        f"Instructions:\n"
        f"1. This is your task: {task}.\n"
        f"2. RESPOND ONLY WITH FILE NAMES AND NEW OR UPDATED CODE.\n"
        f"3. If your task requires a previous agent's response, these are the previous agents' responses: {responses}.\n"
        f"4. If your task requires original code, use these files and their code as reference: {code}.\n"
    )
    time.sleep(2)
    tokens = check_token_count(prompt)
    print(f"Agent Input Token Amount: {tokens}")
    if model == "oai":
        response = await call_openai(prompt)
        yield response
    else:
        # Stream response from the custom C++ model
        async for chunk in stream_call_llm(prompt):
            yield chunk


def fix_json_string(input_string):
    # Fix the FILE_CODE sections to properly escape quotes and handle special characters
    json_string = re.sub(
        r'("FILE_CODE":\s*")(.*?)(?<!\\)("})',
        lambda m: m.group(1) + m.group(2).replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r') + m.group(3),
        input_string,
        flags=re.DOTALL
    )

    try:
        # Replace other problematic parts in the input string
        fixed_string = json_string \
            .replace('"{{', '"{') \
            .replace('}}"', '}"') \
            .replace('}{', '},{') \
            .replace('[[', '[') \
            .replace(']]', ']') \
        # Ensuring the structure is correct
        if not fixed_string.startswith('['):
            fixed_string = '[' + fixed_string
        if not fixed_string.endswith(']'):
            fixed_string = fixed_string + ']'
            fixed_string = fixed_string.replace('] ]', ']')

        return fixed_string
    except json.JSONDecodeError as e:
        print("Error still persists:", e)
        return None


async def produce_final_solution(user_prompt, file_list, agent_responses, original_code, model="oai"):
    prompt = (
        'Instructions:\n'
        '1: You are an expert programmer who will compile original code and updated code into one final version for each file.\n'
        '2: You will only respond using this JSON format: [{"FILE_NAME":"file_name1", "FILE_CODE":"file_code1"}, {"FILE_NAME":"file_name2", "FILE_CODE":"file_code2"}] \n'
        '2.1: FILE_CODE will only be the code of the FILE_NAME associated with it.\n'
        f'2.2: These are the file names: [{file_list}].\n'
        f'2.3: Original file codes: [{original_code}].\n'
        f'2.4: Here are the agent responses you will reference to update the code: {agent_responses}\n'
    )
    tokens = check_token_count(prompt)
    print(f"Final Solution Token Amount INPUT: {tokens}")
    # response = await call_openai(prompt, model="gpt-4o")
    if model == "oai":
        response = await call_openai(prompt)
        response = response.replace("```", "")
    else:
        time.sleep(8)
        response = await call_llm(prompt, tokens*1.8)
    print(f"Final solution OUTPUT: {check_token_count(response)}")
    try:
        index = response.index("[")
        response = response[index:]
        response = response.replace("[\n", "[")
        response = json.loads(response)
        response = await create_unit_tests(response, model)
        return response
    except Exception as exc:
        print(f'Could not parse String Into JSON ERROR. Will Remove all formatting: {exc}')
        try:
            response = fix_json_string(response)
            response = json.loads(response)
            response = await create_unit_tests(response, model)
            return response
        except json.JSONDecodeError:
            return response


def find_file_by_name(agent_response_list, file_name):
    result = [file for file in agent_response_list if file["FILE_NAME"] == file_name]
    return result[0] if result else None


async def create_unit_test_for_file(file, model="oai"):
    try:
        prompt = (
            'INSTRUCTIONS: '
            '1. You will be creating unit tests based on file code. DO NOT INCLUDE ANY EXPLANATION.'
            '2. You will only respond with complete unit test code.'
            f'3. You will create test code based on this code: {file.get("FILE_CODE")}'
        )
        print(f"UNIT TEST CREATION FOR:\n{file.get('FILE_NAME')}\nINPUT TOKEN AMOUNT: {check_token_count(prompt)}")
        if model == "oai":
            response = await call_openai(prompt)
        else:
            response = await call_llm(prompt, 3000)
        file.get("FILE_NAME")
        test_name = "test_" + file.get("FILE_NAME")
        file_code = response.replace("'''python","").replace("'''", "")
        print(f"OUTPUT TOKEN AMOUNT: {check_token_count(response)}")
        return {"FILE_NAME": test_name, "FILE_CODE":file_code}
    except Exception as exc:
        print(exc)
        return None


async def create_unit_tests(file_list, model):
    tasks = [create_unit_test_for_file(file, model) for file in file_list]
    responses = await asyncio.gather(*tasks)
    files = [response for response in responses if response is not None]
    return file_list + files


async def call_openai(prompt, model="gpt-4o"):
    client = OpenAI(api_key=openai_key)
    response = await asyncio.to_thread(client.chat.completions.create,
                                       model=model,
                                       messages=[{"role": "user", "content": prompt}])
    return response.choices[0].message.content


async def call_llm(prompt, output_tokens=6000, extension="/ask_a_pro", url=llm_url):
    # return await call_cpp(prompt, output_tokens)

    time.sleep(2)
    print(check_token_count(prompt))
    # return await call_openai(prompt)
    try:
        headers = {
            'token': 'fja0w3fj039jwiej092j0j-9ajw-3j-a9j-ea'
        }
        response = requests.post(
            url + extension,
            json={
                "output_tokens": output_tokens,
                "prompt": prompt
            },
            headers=headers
        )
        response.raise_for_status()  # Ensure we raise an error for bad responses
        print(response.json()["choices"][0]["finish_reason"])
        print(response.json()["timings"]["predicted_n"])
        response = (response.json()["choices"][0]["message"]["content"]
                    .replace("<|im_end|>", "")
                    .replace("<|im_start|>", "").replace("assistant", " ")
                    .replace('}, {"role": "User", "content": ', ''))
        return response
    except requests.RequestException as exc:
        print(exc)
        raise HTTPException(status_code=500, detail=f"Failed to reach {url}\n{exc}")


async def customized_response(prompt):
    return await call_openai(prompt, model="gpt-4o")


def encode_image(image):
    return base64.b64encode(image.file.read()).decode('utf-8')


async def image_to_text(prompt, image):
    base64_image = encode_image(image)
    client = OpenAI(api_key=openai_key)
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    },
                ],
            }
        ],
        max_tokens=2000,
    )
    return response.choices[0].message.content
