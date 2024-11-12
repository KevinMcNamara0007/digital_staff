import {askPro, generateDataAPI, repoOperationAPI, showDiff, solutionAPI} from "../../api/Axios";
import parse, {attributesToProps} from "html-react-parser";
import DOMPurify from "dompurify";

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
    return await repoOperationAPI(user_prompt, https_clone_link, original_code_branch, new_branch_name, "oai", "no")
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

export const createNewFiles = async (user_prompt, file_list, new_branch_name, repo_dir, agent_responses, code = "") => {
    return await solutionAPI(user_prompt, file_list, new_branch_name, repo_dir, agent_responses, code, "oai")
        .then((response) => {
            return response.data
        }).catch((err) => {
            return []
        })
}

export const getGitChanges = async (repo_dir, produced_code) => {
    return await showDiff(repo_dir, produced_code)
        .then((response) => {
            return response.data
        }).catch((err) => {
            return null
        })
}
//DATA FUNCTIONS

export const dataGenerate = async(dataDescription, rows, input, label) => {
    return await generateDataAPI(dataDescription, rows, ["input:"+input,"label:"+label], "oai")
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

//Content Functions

export const getContentReviewPrompt = (description, content, style, tone) => {
    return ("Instructions:" +
        " 1. You are a peer reviewer of content for the style: " + style + "." +
        " 2. You will give meaningful instructions on where to improve the referenced content." +
        " 3. You will also provide instructions on where to improve this tone: " + tone +
        " 4. Also complete this user ask: " + description + "" +
        "5. This is the referenced content:\n " + content)
}

export const finalDraftPrompt = (description, content, style, tone, review) => {
    return ("Instructions:" +
        "1. You are an expert " + style + " writer." +
        "2. You will fix the referenced content and create a final draft based on these instructions: " + review +
        "3. This is the referenced content: " + content
    )
}


// <Editor data={response} setData={setResponse}/>
// const options = {
//     replace: domNode => {
//         if(domNode.attribs && domNode.name === 'a'){
//             const props = attributesToProps(domNode.attribs)
//             let url = props['href']
//             if(props && url){
//                 let fullUrl = url.match(/^(https?)/g);
//                 if(!fullUrl){
//                     let newUrl = "//"+url
//                     domNode.attribs = {...domNode.attribs, 'href':newUrl}
//                 }
//             }
//         }
//     }
// }
// const callParse = (txt) => {
//     try{
//         const purify = DOMPurify(window);
//         let cleanHTMLTxt = purify.sanitize(txt);
//         let parsed = parse(cleanHTMLTxt, options)
//         return parsed
//     }
//     catch(error){
//         return "error occured while parsing html. please try again"
//     }
// }
//
// const exportToDoc = (data, type) => {
//     let bodyContent = "";
//     let filename = "";
//     if(type === mapper.review){
//         bodyContent = data.replaceAll("\n","<br/>")
//         filename = "review.doc"
//     }else{
//         bodyContent = data;
//         filename = "finaldraft.doc"
//     }
//     let preHtml =
//         "<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'><head><meta charset='utf-8'><title>Export HTML To Doc</title></head><body>";
//     let postHtml = "</body></html>";
//     let html = preHtml + bodyContent + postHtml
//
//     let docMimeType = 'application/vnd.ms-word';
//     let hrefUrl = 'data:'+docMimeType+';charset=utf-8,' + encodeURIComponent(html)
//
//     if(window.navigator.msSaveOrOpenBlob){
//         var blob = new Blob(["\ufeff", html], {
//             type: "application/msword",
//         });
//         window.navigator.msSaveOrOpenBlob(blob, filename)
//     }else{
//         let downloadLinkEle = document.createElement('a')
//         let downloadHelperDiv = document.getElementById('downloadHelper')
//         downloadHelperDiv.appendChild(downloadLinkEle)
//         downloadLinkEle.href = hrefUrl
//         downloadLinkEle.download = filename
//         downloadLinkEle.click()
//         downloadHelperDiv.removeChild(downloadLinkEle)
//     }
// }