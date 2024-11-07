import {askPro, generateDataAPI, repoOperationAPI} from "../../api/Axios";

export const classify = async (userInput) => {
    let prompt = "Instruction: 1. Classify this prompt as a developer, data, general, or content." +
        "2. The prompt is this: " + userInput + "" +
        "3. Only respond with the single word which is one of the following: developer, data, general, content." +
        "4. Note: content deals with rewriting papers, or other text content."
    return await askPro(prompt, 100).then((resp) => {
        let response = resp.data.choices[0].message.content
        if (response.toLowerCase().includes("general")) {
            return "General"
        }
        if (response.toLowerCase().includes("developer")) {
            return "Developer"
        }
        if (response.toLowerCase().includes("data")) {
            return "Data"
        }
        if (response.toLowerCase().includes("content")) {
            return "Content"
        }
    }).catch((err) => {
        return "General"
    })
}

//General
export const askDifferentlyPrompt = (input) => {
    return "Respond only with an alternate way of saying this: " + input
}

export const askLLM = async (prompt) => {
    return await askPro(prompt).then((response) => {
        return response.data.choices[0].message.content
    }).catch((err)=>{
        return null
    })
}


// DEVELOPER FUNCTIONS
export const classifyRepoRequired = async (input) => {
    prompt = "Instructions: " +
        "1. Determine if the user input requires a code repository or not." +
        "2. You will respond only with either 'Yes' or 'No'." +
        "3. If there is no mention of a user repo then the result will be 'No'." +
        "4. If you are not sure if the user is asking to update his existing code, the result will always be 'No'." +
        "5. This is the the users input: " + input + ""
    if(input.toLowerCase().includes("my repo") || input.toLowerCase().includes("update my existing code")){
        return "yes"
    }else{
        return await askPro(prompt, 100).then((resp)=>{
            let response = resp.data.choices[0].message.content
            if(response.toLowerCase().includes("yes")){
                return "yes"
            }else{
                return "no"
            }
        })
    }
}

export const getRepoDetails = async (user_prompt, https_clone_link, original_code_branch, new_branch_name) =>{
    return await repoOperationAPI(user_prompt, https_clone_link, original_code_branch, new_branch_name, "elf", "no")
        .then((resp)=>{
            return resp.data
        }).catch((err)=>{
            console.log(err)
        })
}

export const getDevPlanPrompt = (user_prompt) => {
    return "Instructions: ONLY PROVIDE A list of requirements and steps in order to complete this task: " + user_prompt
}

export const executePlanPrompt =  (user_prompt, files) => {
    let file_codes = ""
    files.forEach((file)=>{
        file_codes = file_codes + "\n" + file.FILE_CODE + "\n"
    })
    return "Instructions:" +
        " 1. You will update existing code to implement these changes: " + user_prompt +
        " 2. Only respond with file names and code. Do not include any explanation." +
        " 3. Make the required changes to this existing code: " + file_codes
}

//DATA FUNCTIONS

export const dataGenerate = async(dataDescription, rows, input, label) => {
    return await generateDataAPI(dataDescription, rows, ["input:"+input,"label:"+label], "elf")
        .then((response)=>{
            if(!response){
                throw new Error("Error")
            }
            let data = response.data
            return data
        }).catch((err)=>{
            console.log(err)
            return []
        })
}