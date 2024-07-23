import asyncio
import base64
import json
import requests
from fastapi import HTTPException
from openai import OpenAI
from src.utilities.general import llm_url, openai_key, check_token_count
import re


def manager_development_agent_prompts(user_prompt, assets, software_type):
    return [
        f"You are an expert {software_type} developer. {user_prompt}, produce ONLY complete code.",
        f"Review the following for accuracy and completeness: {user_prompt}, produce ONLY complete code.",
        f"Review the following for bugs and vulnerabilities and code smells: {user_prompt}, produce ONLY complete code.",
        f"Add inline code comments for all key variables and methods. Produce ONLY complete code.",
        f"You are an expert {software_type}. Inspect and optimize code, correct where needed and produce complete code."
    ]


async def agent_task(task, responses, code):
    print(f"Agent Task: {task}")
    prompt = (
        f"<|im_start|>Instructions:\n"
        f"1. This is your task: {task}.\n"
        f"2. If your task requires a previous agent's response, these are the previous agents' responses: {responses}.\n"
        f"3. If your task requires original code, use these files and their code as reference: {code}.\n"
        f"4. RESPOND ONLY WITH FILE NAMES AND NEW OR UPDATED CODE.<|im_end|>"
    )
    print(f"Agent Input Token Amount: {check_token_count(prompt)}")
    response = await call_llm(prompt, 10000)
    print(f"Agent Output Token Amount: {check_token_count(response)}")
    return response


async def compile_agent_code(task, shot1, shot2, original_code):
    print(f"Compile Agent Shots")
    prompt = (
        f"<|im_start|>Instructions:\n"
        f"1. Version 1 and Version 2 are two different outputs of the task.\n"
        f"2. Compile and Merge both versions into one singular best answer based on the task.\n"
        f"2. Ensure the task was fulfilled: {task} .\n"
        f"2. ONLY RESPOND WITH BEST OUTPUT CODE.\n"
        f"3. Version 1 code: {shot1}.\n"
        f"4. Version 2 code: {shot2}.\n<|im_end|>"
    )
    print(f"Compile Input Token Amount: {check_token_count(prompt)}")
    response = await call_llm(prompt, 10000)
    print(f"Compile Output Token Amount: {check_token_count(response)}")
    return response


async def produce_final_solution(user_prompt, file_list, agent_responses, original_code):
    prompt = (
        '<|im_start|>Instructions:\n'
        '1. You are an expert programmer.\n'
        '2. You will compile all agent code for each corresponding file and place it into a JSON format.\n'
        '3. You will only respond using this JSON format: [{"FILE_NAME":"file_name1", "FILE_CODE":"file_code1"}, {"FILE_NAME":"file_name2", "FILE_CODE":"file_code2"}].\n'
        f'4. FILE_CODE will only be the code of the FILE_NAME associated with it.\n'
        f'5. These are the original file names: [{file_list}], and all file code: [{original_code}].\n'
        f'6. Here are the agent responses you will reference to update the code: {agent_responses}\n'
        '7. Ensure that the JSON is correctly formatted and includes all file names and their corresponding code.'
        '8. DO NOT INCLUDE ANY EXPLANATION, ONLY RESPOND WITH THE JSON FORMAT REQUESTED. <|im_end|>'
    )
    tokens = check_token_count(prompt)
    print(f"Final Solution Token Amount INPUT: {tokens}")
    # response = await call_openai(prompt, model="gpt-4o")
    response = await call_llm(prompt, 10000)
    print(f"Final solution OUTPUT: {check_token_count(response)}")
    try:
        response = json.loads(clean_json_response(response))
        response = await create_unit_tests(response)
        return response
    except json.JSONDecodeError as exc:
        print(f'Could not parse String Into JSON ERROR. Will Remove all formatting: {exc}')
        response = clean_json_response(response)
        try:
            response = json.loads(response.replace("\n", ""))
            response = await create_unit_tests(response)
            return response
        except json.JSONDecodeError:
            response = await call_openai(prompt)
            response = response.replace('"""', '').replace("```json", '').replace("```", '')
            try:
                response = json.loads(response)
                response = await create_unit_tests(response)
                return response
            except json.JSONDecodeError:
                print("Removing Formatting Did not help final response, trying again...")
                return response
                # return await produce_final_solution(user_prompt, file_list, agent_responses, original_code)


async def produce_final_solution_for_file(file, agent_responses):
    prompt = (
        "<|im_start|>Instructions:\n"
        "1. You are an expert programmer.\n"
        f"2. You will compile all agent code for the following file {file}.\n"
        "3. You will respond only with the completed compiled and merged code.\n"
        f"4. Here are the agent responses you will reference when making the final version of the code: {agent_responses}\n<|im_end|>"
    )
    print(f"Final Solution Token Amount INPUT: {check_token_count(prompt)}")
    response = await call_llm(prompt, 2000)
    print(f"Final solution OUTPUT: {check_token_count(response)}")
    return response.replace("```java", "").replace("```python", "").replace("```", "")


async def process_file(file, agent_response_list):
    responses_for_file = find_file_by_name(agent_response_list, file)
    if responses_for_file is not None:
        file_solution = await produce_final_solution_for_file(file, responses_for_file)
        obj = {"FILE_NAME": file, "FILE_CODE": file_solution}
        file_test = await create_unit_test_for_file(obj)
        return [obj] + ([file_test] if file_test is not None else [])
    return []


async def produce_final_solution_for_large_repo(user_prompt, file_list, agent_responses, original_code):
    final_list = []
    try:
        agent_response_list = json.loads(agent_responses)
        tasks = [process_file(file, agent_response_list) for file in file_list]
        results = await asyncio.gather(*tasks)
        for result in results:
            final_list.extend(result)
        return final_list
    except json.JSONDecodeError as exc:
        print(f"Could not produce final solution: {exc}")
        return "Fail"


def find_file_by_name(agent_response_list, file_name):
    result = [file for file in agent_response_list if file["FILE_NAME"] == file_name]
    return result[0] if result else None


async def create_unit_test_for_file(file):
    prompt = (
        '<|im_start|>INSTRUCTIONS: '
        '1. You will be creating a unit test file based on file code.'
        '2. You will only respond in JSON Format: {"FILE_NAME":"file_name1", "FILE_CODE":"file_code1"} .'
        f'3. FILE_NAME will be "test_" + {file.get("FILE_NAME")}.'
        f'4.FILE_CODE MUST ONLY BE UNIT TEST CODE. You will create unit tests based on this code: {file.get("FILE_CODE")}<|im_end|>'
    )
    try:
        print(f"UNIT TEST CREATION FOR:\n{file.get('FILE_NAME')}\nINPUT TOKEN AMOUNT: {check_token_count(prompt)}")
        response = await call_llm(prompt, 2000)
        print(f"OUTPUT TOKEN AMOUNT: {check_token_count(response)}")
        try:
            response = json.loads(clean_json_response(response))
            return response
        except json.JSONDecodeError as exc:
            print(f'JSON ERROR FOR TEST FILE {file.get("FILE_NAME")}. Will not add due to: {exc}')
            return None
    except Exception as exc:
        print(exc)
        return None


async def create_unit_tests(file_list):
    tasks = [create_unit_test_for_file(file) for file in file_list]
    responses = await asyncio.gather(*tasks)
    files = [response for response in responses if response is not None]
    return file_list + files


def clean_json_response(input_string):
    # Remove leading and trailing whitespace
    input_string = input_string.strip()
    # Define the substrings to replace
    substrings_to_replace = [
        ",{\\n    wLock.unlock();\\n    }",
        ",{\\n    rwl.readLock().unlock();\\n    },"
    ]
    # Replace each substring with an empty string
    for substring in substrings_to_replace:
        input_string = input_string.replace(substring, "")
    # Correctly escape the remaining newline characters
    input_string = input_string.replace('\n', '\\n')
    input_string = re.sub(r'""', '\\"', input_string)
    # Fix issues with single backslashes by replacing them with double backslashes
    input_string = input_string.replace('\\', '\\\\')

    # Ensure that embedded double quotes are correctly escaped
    input_string = input_string.replace('"', '\\"')
    # Parse the cleaned string as JSON
    return input_string


async def call_openai(prompt, model="gpt-4o"):
    client = OpenAI(api_key=openai_key)
    response = await asyncio.to_thread(client.chat.completions.create,
                                       model=model,
                                       messages=[{"role": "user", "content": prompt}])
    return response.choices[0].message.content


async def call_llm(prompt, output_tokens=2000, url=llm_url):
    return await call_cpp(prompt, output_tokens)
    # try:
    #     response = requests.post(
    #         url,
    #         data={
    #             "prompt": prompt,
    #             "temperature": 0.50,
    #             "max_output_tokens": output_tokens,
    #             "messages": ""
    #         }
    #     )
    #     response.raise_for_status()  # Ensure we raise an error for bad responses
    #     return response.json()["choices"][0]["message"]["content"].replace("<|im_end|>", "").replace("<|im_start|>", "").replace("assistant", " ")
    # except requests.RequestException as exc:
    #     raise HTTPException(status_code=500, detail=f"Failed to reach {url}\n{exc}")


async def call_cpp(prompt, output_tokens=9000, url="http://127.0.0.1:8001/completion"):
    try:
        response = requests.post(
            url,
            json={
                "prompt": prompt,
                "temperature": 0.50,
                "max_output_tokens": output_tokens,
                "messages": ""
            }
        )
        response.raise_for_status()  # Ensure we raise an error for bad responses
        return response.json()["content"].replace("<|im_end|>", "").replace("<|im_start|>", "").replace("assistant", " ")
    except requests.RequestException as exc:
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
