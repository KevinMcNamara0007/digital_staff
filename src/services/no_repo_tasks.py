import json

from src.utilities.general import file_filter
from src.utilities.inference2 import call_openai, manager_development_agent_prompts, agent_task, produce_final_solution, \
    image_to_text, call_llm, clean_json_response


async def manager_development_base_service(user_prompt, file):
    # Create Code Project
    if file is None:
        code_prompt = ("INSTRUCTIONS:"
                       f" 1. You will create only code based on the user ask: {user_prompt}."
                       f"2. Respond only with code. Do not include any reasoning or explanation.")
        code = await call_llm(code_prompt, 7000)
        file_prompt = (f"INSTRUCTIONS: "
                       f"1. Give this code a filename: {code}."
                       f"2. Respond only with the filename.")
        file = await call_llm(file_prompt, 100)
        files = [file]
        language_prompt = ("INSTRUCTIONS: "
                           f"1. What is the programming language of this file: {str(files)}")
        language = await call_llm(language_prompt, 100)
        code_foundation = {
            "FILE_NAMES": files,
            "ALL_CODE": code,
            "CODE_LANGUAGE": language
        }
        return {"CODE_FOUNDATION": code_foundation, "MANAGER_PLAN": manager_development_agent_prompts(user_prompt, file_filter(files), language)}
    else:
        # Image Diagram Route
        prompt = (f'Instructions: 1. You will create a code project based on this user ask: {user_prompt}.'
                  '2. RESPOND ONLY IN THIS JSON FORMAT: {"FILE_NAMES": [filename1,filename2],"ALL_CODE": "","CODE_LANGUAGE": ""}'
                  '3. DO NOT INCLUDE ANY EXPLANATION. give files names yourself for FILE_NAMES, produce only code for ALL_CODE, and give the language of the program for CODE_LANGUAGE.')
        code_foundation = await image_to_text(prompt, file)
        code_foundation = code_foundation.replace("```", '').replace('json', '').replace("assistant", "").replace("<|im_start|>", "").replace("\n", "")
        try:
            index = code_foundation.index("{")
            code_foundation = code_foundation[index:]
            print(code_foundation)
            parsed_foundation = json.loads(code_foundation)
            return {"CODE_FOUNDATION": parsed_foundation, "MANAGER_PLAN": manager_development_agent_prompts(user_prompt, file_filter(parsed_foundation.get("FILE_NAMES")), parsed_foundation.get("CODE_LANGUAGE"))}
        except json.JSONDecodeError as exc:
            print(f"Failed to Parse, code foundation corrupt due to: {exc}\n\nTrying Again")
            return await manager_development_base_service(user_prompt, file)


async def no_repo_agent_task_service(task, responses, code):
    return {"agent_response": await agent_task(task, responses, code)}

async def no_repo_produce_solution(user_prompt, file_list, responses, code):
    return await produce_final_solution(user_prompt, file_list, responses, code)