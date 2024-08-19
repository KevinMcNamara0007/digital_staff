import axios from 'axios'

const axiosFormData = axios.create({
    baseURL: "http://127.0.0.1:8080",
    headers: {
        "Content-Type": "multipart/form-data"
    }
})

const axiosJSON = axios.create({
    baseURL: "http://127.0.0.1:8080",
    headers: {
        "Content-Type": "application/json"
    }
})

function postJSON(url, data){
    return axiosJSON({
        method: 'post',
        body: JSON.stringify(data)
    })
}
function postFormData(url,data){
    return axiosFormData({
        method: 'post',
        url,
        data
    })
}

export const repoOperationAPI = (user_prompt, https_clone_link, original_code_branch, new_branch_name, model, flow="no") => {
    let data = new FormData()
    data.set("user_prompt", user_prompt);
    data.set("https_clone_link", https_clone_link);
    data.set("original_code_branch", original_code_branch);
    data.set("new_branch_name", new_branch_name);
    data.set("model", model);
    data.set("flow", flow);
    return postFormData("/Tasks/repo_ops", data)
}

export const managerPlanAPI = (user_prompt, original_code_branch, new_branch_name, model, file_list, repo_dir,file, flow="no") => {
    let data = new FormData()
    data.set("user_prompt", user_prompt);
    data.set("original_code_branch", original_code_branch);
    data.set("new_branch_name", new_branch_name);
    data.set("model", model);
    data.set("file_list", file_list);
    data.set("repo_dir", repo_dir);
    data.set("flow", flow);
    file !== null && data.set("file",file)
    return postFormData("/Tasks/manager_plan", data)
}

export const agentTaskAPI = (user_prompt, file_list, agent_task, new_branch_name, repo_dir, agent_responses, code, model, flow="no") => {
    let data = new FormData()
    data.set("user_prompt", user_prompt);
    data.set("file_list", file_list);
    data.set("agent_task", agent_task);
    data.set("agent_responses", agent_responses);
    data.set("new_branch_name", new_branch_name);
    data.set("repo_dir", repo_dir);
    data.set("code", code);
    data.set("model", model);
    data.set("flow", flow);
    return postFormData("/Tasks/agent_task", data)
}

export const solutionAPI = (user_prompt, file_list, new_branch_name, repo_dir, agent_responses, code, model, flow="no") => {
    let data = new FormData()
    data.set("user_prompt", user_prompt);
    data.set("file_list", file_list);
    data.set("agent_responses", agent_responses);
    data.set("new_branch_name", new_branch_name);
    data.set("repo_dir", repo_dir);
    data.set("model", model);
    data.set("flow", flow);
    data.set("code", code);
    return postFormData("/Tasks/produce_solution", data)
}


export const showDiff = (repo_dir, produced_code) => {
    let data = {
        "produced_code": produced_code,
        "repo_dir":repo_dir
    }
    return postJSON("/Tasks/show_diff", data)
}