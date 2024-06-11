import json
import requests
import json
import uuid
import asyncio
from src.utilities.general import manifest, llm_url

def manager__development_agent_prompts(user_prompt, file_list):
    tasks = [
        f"complete the ask of {user_prompt} using the following files: {file_list}.",
        f"review agent 1 code and certify that agent 1 fulfilled the ask of: {user_prompt}. If the ask is not completed, complete the ask.",
        f"review agent 1 and agent 2 code. Certify that both agents fulfilled the ask of: {user_prompt}. If the ask is not completed, complete the ask.",
        "fix all major bugs, vulnerabilities and code smells from agent 1, 2, and 3.",
        "review and update agent code for security if needed.",
        f"update the unit test code. If there is no unit test code, create unit tests for the following files {file_list} and agent code.",
        "inspect all agent code and unit test code from agents for faults and fix where needed."
    ]
    return [
        {f"instruction {i+1}": f"You are a software engineer. You are asked to {task}"}
        for i, task in enumerate(tasks)
    ]

async def agent_task(task, responses, code):
    prompts = [
        {"instruction": "This is your task", "content": task},
        {"instruction": "You will ONLY RESPOND with the updated code."},
        {"instruction": "You will not provide any explanation to any of the code."},
        {"instruction": "If there is nothing needed to be updated, please respond with: NA."},
        {"instruction": "If your task requires a previous agent's response, these are the previous agents' responses:", "content": responses},
        {"instruction": "If your task requires original code, use these files and their code as reference:", "content": code}
    ]
    return call_llm(prompts, "none")

async def produce_final_solution(user_prompt, file_list, agent_responses, original_code):
    prompt = {
        "instruction 1": f"You are an elite coder assigned to complete the ask of this: {user_prompt}.",
        "instruction 2": f"Your coding agents have helped you with certain tasks, use their answers as reference: [{agent_responses}].",
        "instruction 3": f"This was the original code used to complete the agents' tasks: ['{original_code.replace('"', "'")}'].",
        "instruction 4": f"These were the exact file names used: {file_list}.",
        "instruction 5": "Using the responses of your agents and the original code, you will complete the user's ask by producing a final code solution for each file and its code.",
        "instruction 6": "File code must only be code of type which is related to the extension of the file name.",
        "instruction 7": 'YOU WILL RESPOND ONLY IN THIS JSON FORMAT EXAMPLE: "File1": {"FILE_NAME":"", "FILE_CODE":""}, "File2": {"FILE_NAME":"", "FILE_CODE":""}.'
    }
    response = call_llm([prompt], "none")
    response = response.replace('""', '')
    try:
        response = json.loads(response)
    except json.JSONDecodeError as exc:
        print(f'Could not parse String Into JSON ERROR: {exc}')
    return response

def call_llm(prompts, rules="You are a Digital Assistant.", url=llm_url):
    try:
        data = {
            "prompt": json.dumps([{"role": "system", "content": rules}] + [{"role": "user", "content": prompt} for prompt in prompts]),
            "temperature": 0.05
        }
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as exc:
        raise HTTPException(status_code=500, detail=f"Failed to reach {url}\n{exc}")

################################### Net New code to manage chain of custody between agents ###################################

# this is the code that will be used to manage the chain of custody between agents
async def chain_of_custody(assets, action, customer_id, session_id, inventory_updates=None):
    """
    Edits, deletes, or adds new inventory items to the inventory section of a specific asset JSON object 
    based on the provided action and parameters.
    
    :param assets: A list of JSON objects representing the assets to be edited.
    :param action: The action to perform: "edit", "delete", or "new".
    :param customer_id: The customer ID of the asset to be edited.
    :param session_id: The session ID of the asset to be edited.
    :param inventory_updates: A list of dictionaries with updates for the inventory.
    :return: The updated list of JSON objects.
    """
    if not isinstance(assets, list):
        raise ValueError('Assets must be a list of JSON objects.')

    # Check if the action is valid.
    updated_assets = []

    # validate the action and update the assets accordingly.
    for asset in assets:
        if isinstance(asset, str):
            try:
                asset = json.loads(asset)
            except json.JSONDecodeError as exc:
                raise ValueError(f'Invalid JSON data provided: {exc}')

        if (asset['asset']['customer_id'] == customer_id and 
            asset['asset']['session_id'] == session_id):
            
            if action == "edit":
                if inventory_updates is not None:
                    if not isinstance(inventory_updates, list):
                        raise ValueError('Inventory updates must be a list of dictionaries.')
                    asset['asset']['inventory'] = inventory_updates

            elif action == "delete":
                asset['asset']['inventory'] = []

            elif action == "new":
                if inventory_updates is not None:
                    if not isinstance(inventory_updates, list):
                        raise ValueError('New inventory must be a list of dictionaries.')
                    asset['asset']['inventory'].extend(inventory_updates)
                else:
                    asset['asset']['inventory'].append({
                        "filename1": "",
                        "code1": "",
                        "filename2": "",
                        "code2": ""
                    })

            else:
                raise ValueError(f"Invalid action: {action}. Action must be 'edit', 'delete', or 'new'.")

        updated_assets.append(asset)

    return updated_assets

# Example usage
original_assets = [
    {
        "asset": {
            "session_id": "abc123",
            "customer_id": "cust001",
            "inventory": [
                {
                    "filename1": "file1.py",
                    "code1": "print('Hello World!')",
                    "filename2": "file2.py",
                    "code2": "print('Goodbye World!')"
                }
            ]
        }
    },
    {
        "asset": {
            "session_id": "def456",
            "customer_id": "cust002",
            "inventory": [
                {
                    "filename1": "file3.py",
                    "code1": "print('Sample Code')",
                    "filename2": "file4.py",
                    "code2": "print('More Sample Code')"
                }
            ]
        }
    }
]

# Example of how you might call the function in an async context
# async def main():
#     updated_assets = await chain_of_custody(
#         original_assets,
#         action="edit",
#         customer_id="cust001",
#         session_id="abc123",
#         inventory_updates=[
#             {"filename1": "file5.py", "code1": "print('New Code')", "filename2": "file6.py", "code2": "print('More New Code')"}
#         ]
#     )
#     print(json.dumps(updated_assets, indent=4))

# # Run the example
# asyncio.run(main())
