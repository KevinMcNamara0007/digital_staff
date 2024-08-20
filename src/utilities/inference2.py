import asyncio
import base64
import json
import time

import requests
from fastapi import HTTPException
from openai import OpenAI


from src.utilities.general import llm_url, openai_key, check_token_count
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
        f"2. RESPOND ONLY WITH FILE NAMES AND NEW OR UPDATED CODE."
        f"3. If your task requires a previous agent's response, these are the previous agents' responses: {responses}.\n"
        f"4. If your task requires original code, use these files and their code as reference: {code}.\n"
    )
    time.sleep(2)
    tokens = check_token_count(prompt)
    print(f"Agent Input Token Amount: {tokens}")
    if model == "oai":
        response = await call_openai(prompt)
    else:
        response = await call_llm(prompt, tokens*1.7)
    print(f"Agent Output Token Amount: {check_token_count(response)}")
    return response


# async def compile_agent_code(task, shot1, shot2, original_code):
#     print(f"Compile Agent Shots")
#     prompt = (
#         f"Instructions:\n"
#         f"1. Version 1 and Version 2 are two different outputs of the task.\n"
#         f"2. Compile and Merge both versions into one singular best answer based on the task.\n"
#         f"2. Ensure the task was fulfilled: {task} .\n"
#         f"2. ONLY RESPOND WITH BEST OUTPUT CODE.\n"
#         f"3. Version 1 code: {shot1}.\n"
#         f"4. Version 2 code: {shot2}.\n"
#     )
#     tokens = check_token_count(prompt)
#     print(f"Compile Input Token Amount: {tokens}")
#     response = await call_llm(prompt, tokens*1.7)
#     print(f"Compile Output Token Amount: {check_token_count(response)}")
#     return response

def fix_json_string(input_string):
    try:
        # Replace the problematic parts in the input string
        fixed_string = input_string \
            .replace('\\', '\\\\') \
            .replace('\n', '\\n') \
            .replace('\t', '\\t') \
            .replace('"{{', '"{') \
            .replace('}} "', '}"') \
            .replace('}{', '},{') \
            .replace('[[','[') \
            .replace(']]', ']') \
            .replace('"__main__"',"'__main__'") \
            .replace("n```","") \
            .replace("```python", "")


        # Fix the structure by ensuring it's wrapped correctly
        fixed_string = f'[{fixed_string}]'

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
    print(prompt)
    print(f"Final Solution Token Amount INPUT: {tokens}")
    # response = await call_openai(prompt, model="gpt-4o")
    if model == "oai":
        response = await call_openai(prompt)
    else:
        response = await call_llm(prompt, tokens*1.8)
    print(f"Final solution OUTPUT: {check_token_count(response)}")
    try:
        index = response.index("[")
        response = response[index:]
        response = response.replace("[\n","[")
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
                # return await produce_final_solution(user_prompt, file_list, agent_responses, original_code)


# async def produce_final_solution_for_file(file, agent_responses):
#     prompt = (
#         "Instructions:\n"
#         "1. You are an expert programmer.\n"
#         f"2. You will compile all agent code for the following file {file}.\n"
#         "3. You will respond only with the completed compiled and merged code.\n"
#         f"4. Here are the agent responses you will reference when making the final version of the code: {agent_responses}\n"
#     )
#     tokens = check_token_count(prompt)
#     print(f"Final Solution Token Amount INPUT: {tokens}")
#     time.sleep(5)
#     response = await call_llm(prompt, tokens*1.5)
#     print(f"Final solution OUTPUT: {check_token_count(response)}")
#     return response.replace("```java", "").replace("```python", "").replace("```", "")
#
#
# async def process_file(file, agent_response_list):
#     responses_for_file = find_file_by_name(agent_response_list, file)
#     if responses_for_file is not None:
#         file_solution = await produce_final_solution_for_file(file, responses_for_file)
#         obj = {"FILE_NAME": file, "FILE_CODE": file_solution}
#         file_test = await create_unit_test_for_file(obj)
#         return [obj] + ([file_test] if file_test is not None else [])
#     return []
#
#
# async def produce_final_solution_for_large_repo(user_prompt, file_list, agent_responses, original_code):
#     final_list = []
#     try:
#         agent_response_list = json.loads(agent_responses)
#         tasks = [process_file(file, agent_response_list) for file in file_list]
#         results = await asyncio.gather(*tasks)
#         for result in results:
#             final_list.extend(result)
#         return final_list
#     except json.JSONDecodeError as exc:
#         print(f"Could not produce final solution: {exc}")
#         return "Fail"


def find_file_by_name(agent_response_list, file_name):
    result = [file for file in agent_response_list if file["FILE_NAME"] == file_name]
    return result[0] if result else None


async def create_unit_test_for_file(file, model="oai"):
    prompt = (
        'INSTRUCTIONS: '
        '1. You will be creating unit tests based on file code. DO NOT INCLUDE ANY EXPLANATION.'
        '2. You will only respond with complete unit test code.'
        f'3. You will create test code based on this code: {file.get("FILE_CODE")}'
    )
    try:
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


async def call_llm(prompt, output_tokens=6000, url=llm_url):
    return await call_cpp(prompt, output_tokens)

    time.sleep(2)
    print(check_token_count(prompt))
    # return await call_openai(prompt)
    # return await call_cpp(prompt, output_tokens)
    # try:
    #     headers = {
    #         'token': 'fja0w3fj039jwiej092j0j-9ajw-3j-a9j-ea'
    #     }
    #     response = requests.post(
    #         url,
    #         data={
    #             "prompt": prompt,
    #             "rules": "You are a friendly virtual assistant. Your role is to answer the user questions and follow their instructions. Be concise and accurate.",
    #             "temperature": 0.50,
    #             "top_k": 40,
    #             "top_p": 0.95
    #         },
    #         headers=headers
    #     )
    #     response.raise_for_status()  # Ensure we raise an error for bad responses
    #     print(response.json()["choices"][0]["message"]["content"])
    #     print(response.json()["choices"][0]["finish_reason"])
    #     print(response.json()["timings"]["predicted_n"])
    #     response = (response.json()["choices"][0]["message"]["content"]
    #                 .replace("<|im_end|>", "")
    #                 .replace("<|im_start|>", "").replace("assistant", " ")
    #                 .replace('}, {"role": "User", "content": ', ''))
    #     return response
    # except requests.RequestException as exc:
    #     raise HTTPException(status_code=500, detail=f"Failed to reach {url}\n{exc}")


async def call_cpp(prompt, output_tokens=9000, url="http://127.0.0.1:8001/completion"):
    time.sleep(2)
    hermes = f"<|im_start|>system\n{prompt}<|im_end|>\n<|im_start|>user\n<|im_end|>\nassistant"
    llama = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>{prompt}<|start_header_id|>user<|end_header_id|><|eot_id|>assistant"
    try:
        response = requests.post(
            url,
            json={
                "prompt": llama,
                "stream": False,
                "n_predict": output_tokens,
                "temperature": 0.8,
                "stop":
                    ["</s>",
                     "<|end|>",
                     "<|eot_id|>",
                     "<|end_of_text|>",
                     "<|im_end|>",
                     "<|EOT|>",
                     "<|END_OF_TURN_TOKEN|>",
                     "<|end_of_turn|>",
                     "<|endoftext|>",
                     "assistant",
                     "user"],
                "repeat_last_n":0,
                "repeat_penalty":1,
                "penalize_nl":False,
                "top_k":0,
                "top_p":1,
                "min_p":0.05,
                "tfs_z":1,
                "typical_p":1,
                "presence_penalty":0,
                "frequency_penalty":0,
                "mirostat":0,
                "mirostat_tau":5,
                "mirostat_eta":0.1,
                "grammar":"",
                "n_probs":0,
                "min_keep":0,
                "image_data":[],
                "cache_prompt":False,
                "api_key":""
            }
        )
        response.raise_for_status()  # Ensure we raise an error for bad responses
        print(response.json()["stop"])
        return response.json()["content"]
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
