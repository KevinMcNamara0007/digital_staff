let code = "Here is the cleaned code:\n\ngeneral.py:\n\n```python\ndef add(x, y):\n return x + y\n\ndef subtract(x, y):\n return x - y\n\ndef multiply(x, y):\n return x * y\n\ndef divide(x, y):\n return x / y\n```\n\nutilities/__init__.py:\n\n```python\nimport json\n\nif sys.version_info >= (3, 7):\n def print_colorized_text(text):\n pass\n if not sys.stdout.isattt:\n def colorize(text, color):\n return f\"\\033[{color}m{text}\\033[0m\"\n return colorize(text, \"31\")\n else:\n return text\n else:\n return print_colorized_text\n else:\n pass\n\ndef json_load(json_string):\n return json.loads(json_string)\n```\n\nutilities/git.py:\n\n```python\nimport subprocess\nimport re\n\ndef get_current_branch():\n result = subprocess.run(\"git branch\", shell=True, stdout=subprocess.PIPE).stdout.decode(\"utf-8\").split(\"\\n\")[1:-1] if result else None\n return [i for i in result if not i.startswith(\"*\")][0] if result else None\n\ndef get_git_status():\n result = subprocess.run(\"git status\", shell=True, stdout=subprocess.PIPE).stdout.decode(\"utf-8\")\n return re.search(r\"([\\d\\W]+)\\s+(\\d{2,})[ ]+\\[(.+?)\\]\", result.decode(\"utf-8\")) if result else None\n```\n\nutilities/inference.py:\n\n```python\nimport numpy as np\nimport tensorflow as tf\n\ndef load_model(model_path):\n return tf.keras.models.load_model(model_path)\n\ndef predict(model, input_data):\n if not (isinstance(input_data, np.ndarray) or isinstance(input_data, list)):\n raise TypeError(\"Input data must be a numpy array or a list.\")\n return model.predict(input_data)\n```"
window.onload = function () {
    // document.getElementById("newCode").innerText = code.replaceAll('`')
    document.getElementById("inputs").style.display = "flex"
    document.getElementById("responses").style.display = "none"
    document.getElementById("loader").style.display = "none"
}


function digitalAgentAPI(){
    let formData = new FormData();
    formData.append("user_prompt", document.getElementById("instruction").value);
    formData.append("https_clone_link", document.getElementById("repo").value);
    formData.append("original_code_branch", document.getElementById("branch").value);
    formData.append("new_branch_name", document.getElementById("newBranch").value);
    formData.append("flow", "no")
    displayHideInputs();
    displayHideLoader();
    fetch("/Tasks/repo_ops", {
        method: 'POST',
        body: formData
    }).then(response => {
        console.log(response)
        if(!response.ok){
            displayAlert("Error on clone response")
        }
        return response.json();
    }).then(data => {
        displayHideResponses();
        let completeString = "Files: \n\n" + data.files
        document.getElementById("newCode").innerText = completeString.replaceAll('`')
        managerTasksAPI(formData, data.files, data.repo_dir)
    }).catch(error=>{
        displayHideLoader();
        displayAlert("Git Repo Clone API Failed")
    })
}

function managerTasksAPI(prevData, files, directory){
    prevData.append("file_list", files)
    prevData.append("repo_dir", directory)
    fetch("/Tasks/manager_plan", {
        method: 'POST',
        body: prevData
    }).then(response => {
        console.log(response)
        if(!response.ok){
            displayAlert("Error on manager plan response")
        }
        return response.json();
    }).then(async data => {
        console.log(data)
        let previous = document.getElementById("newCode")
        let completeString = "";
        for (const key of Object.keys(data)) {
            completeString = completeString + "\n\n" + key + "\n\n" + data[key];
        }
        previous.innerText = previous.innerText + "\n\nManager Plan:\n\n" + completeString
        console.log("got here")
        console.log(Object.keys(data))
        previousAgentResponse = ""
        for (const key of Object.keys(data)) {
            await agentTaskAPI(prevData, key, data[key], previousAgentResponse)
        }
        await getFinalSolution(prevData, previousAgentResponse, "");;
    }).catch(error =>{
        displayHideLoader();
        displayAlert("Manager Task API has failed")
    })
}

let previousAgentResponse = "";
async function agentTaskAPI(prevFormData, agent, agentTask, agentResponses){
    prevFormData.append("agent_task", agentTask)
    prevFormData.append("agent_responses", agentResponses)

    let previous = document.getElementById("blocks")
    await fetch("/Tasks/agent_task", {
        method: 'POST',
        body: prevFormData
    }).then(async response => {
        console.log(response)
        if (!response.ok) {
            displayAlert("Error on manager plan response")
        }
        const jsonResponse = await response.json();
        // Create new element to display
        previousAgentResponse = previousAgentResponse + "{" + agent + ":" + await jsonResponse + "},"
        let element = document.createElement('code')
        element.className = "response";
        element.innerText =  agent + " Response:\n" + jsonResponse;
        previous.appendChild(element);
        return jsonResponse;
    }).catch(error =>{
        previousAgentResponse = previousAgentResponse + "{" + agent + ":" + "Failed To Do Task" + "},"
        previous.innerText = previous.innerText + "\n\n\n" + agent + " Response:\n" + "Failed to do Task";
        return "Failed"
        displayAlert("Agent Task has failed")
    })
}

async function getFinalSolution(prevFormData, code){
    prevFormData.append("agent_responses", previousAgentResponse)
    await fetch("/Tasks/produce_solution", {
        method: 'POST',
        body: prevFormData
    }).then(response=>{
        if (!response.ok) {
            displayAlert("Error on Final Solution")
        }
        return response.json();
    }).then(data =>{
        console.log("Final Solution:")
        console.log(data)
        let previous = document.getElementById("blocks")
        let element = document.createElement('code')
        element.className = "response";
        element.innerText =   "\n\nFinal Solution:\n\n" + data;
        previous.appendChild(element);
        displayHideLoader()
    }).catch(error =>{
        displayHideLoader()
    })
}


const delay = ms => new Promise(res => setTimeout(res, ms));
const displayAlert = msg => {
    document.getElementById("popup").style.display = "block";
    document.getElementById("alert").innerText = msg;
    delay(3000).then(()=>{
        document.getElementById("alert").innerText = "";
        document.getElementById("popup").style.display = "none";
    })
}

const displayHideInputs = () =>{
    const inputs = document.getElementById("inputs");
    inputs.style.display = inputs.style.display !== "flex" ? "flex" : "none";
}
const displayHideResponses = () => {
    const responses = document.getElementById("responses");
    responses.style.display = responses.style.display !== "flex" ? "flex" : "none";
}

const displayHideLoader = () => {
    const loader = document.getElementById("loader");
    loader.style.display = loader.style.display !== "flex" ? "flex" : "none";
}

const reset = () => {
    displayHideResponses();
    displayHideInputs();
}