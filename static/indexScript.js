let history = localStorage.getItem("digitalHistory")
    ? JSON.parse(localStorage.getItem("digitalHistory"))
    : [];
let active = 0;
let current = 0;
let repo = false;

window.onload = function () {
    loadSessions()
}

function showRepoSettings(){
    document.getElementById("repoSettings").style.display = "block";
}

function flowChecker(){
    let repoInput = document.getElementById("repo").value;
    if(repoInput === ""){
        repo = false;
        resetColors();
        //HIDE REPO SETTINGS
        document.getElementById("repoSettings").style.display = "none";

        active = history.length;
        current = history.length;
        // new history object
        let object = {
            "title": instruction,
            "plan": "loader",
            "agent1": "loader",
            "agent2": "loader",
            "agent3": "loader",
            "agent4": "loader",
            "agent5": "loader",
            "agent6": "loader",
            "agent7": "loader",
            "solution": []
        }
        history.push(object)

        // Create new session div
        let element = document.createElement('div')
        element.className = "session";
        element.innerText =  document.getElementById("instruction").value;
        element.id = "sesh" + current;
        element.onclick = function(){changeActive(current)};
        document.getElementById("sessions").appendChild(element)

        // Empty Response Div
        document.getElementById("codeBlocks").innerHTML = ""

        //Create Base formdata
        let formData = new FormData();
        formData.append("user_prompt", document.getElementById("instruction").value);
        formData.append("https_clone_link", "none");
        formData.append("original_code_branch", "none");
        formData.append("new_branch_name", "none");
        formData.append("flow", "no")
        // Call Manager API
        managerTasksAPI(formData,"none","none")
    }else{
        repo = true;
        digitalAgentAPI()
    }
}

function digitalAgentAPI(){
    resetColors();
    let formData = new FormData();
    let instruction = document.getElementById("instruction").value;
    formData.append("user_prompt", instruction);
    formData.append("https_clone_link", document.getElementById("repo").value);
    formData.append("original_code_branch", document.getElementById("branch").value);
    formData.append("new_branch_name", document.getElementById("branch").value);
    formData.append("flow", "no")

    //HIDE REPO SETTINGS
    document.getElementById("repoSettings").style.display = "none";

    // Call API
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
        active = history.length;
        current = history.length;
        // new history object
        let object = {
            "title": instruction,
            "plan": "loader",
            "agent1": "loader",
            "agent2": "loader",
            "agent3": "loader",
            "agent4": "loader",
            "agent5": "loader",
            "agent6": "loader",
            "agent7": "loader",
            "solution": []
        }
        history.push(object)

        // Create new session div
        let element = document.createElement('div')
        element.className = "session";
        element.innerText =  instruction;
        element.id = "sesh" + current;
        element.onclick = function(){changeActive(current)};
        document.getElementById("sessions").appendChild(element)

        // Empty Response Div
        document.getElementById("codeBlocks").innerHTML = ""

        // Get Manager Plan
        managerTasksAPI(formData, data.files, data.repo_dir)
    }).catch(error=>{
        displayAlert("Git Repo Clone API Failed" + error)
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
        if(repo === true){
            //Get Entire Manager Plan
            let completeString = "";
            data.forEach(function (prompt, index) {
                completeString = completeString + "\n\nAgent " + (index+1) + "\n\n" + prompt;
                index++;
            });
            //Update Manager Plan in history
            history[current].plan = "Files to use:\n\n" + files + "\n\n" + completeString;
            //Display Manager Plan
            // Create new session div
            let element = document.createElement('div')
            element.className = "response";
            element.innerHTML =  '<div class="title">Developer Plan</div>' + '<div class="agentAnswer">' + history[current].plan + '</div>';
            document.getElementById("codeBlocks").appendChild(element)

            previousAgentResponse = ""
            let index = 0;
            for (const prompt of data) {
                index++;
                if(index === 1){
                    document.getElementById("1").style.backgroundColor = "#e37508";
                }else{
                    console.log((index-1).toString())
                    document.getElementById((index-1).toString()).style.backgroundColor = "#3b7c35";
                    document.getElementById((index).toString()).style.backgroundColor = "#e37508";
                }
                await agentTaskAPI(prevData, ("agent " + (index)), prompt, previousAgentResponse, index)
            }
            // Final Solution
            document.getElementById((index).toString()).style.backgroundColor = "#3b7c35";
            await getFinalSolution(prevData, previousAgentResponse, "");
        }else{
            //Get Entire Manager Plan
            let manager_plan = data.MANAGER_PLAN;
            let completeString = "\n" + "Files:\n\n" + data.CODE_FOUNDATION.FILE_NAMES;
            manager_plan.forEach(function (prompt, index) {
                completeString = completeString + "\n\nAgent " + (index+1) + "\n\n" + prompt;
                index++;
            });
            //Update Manager Plan in history
            history[current].plan = completeString;
            //Display Manager Plan
            // Create new session div
            let element = document.createElement('div')
            element.className = "response";
            element.innerHTML =  '<div class="title">Developer Plan</div>' + '<div class="agentAnswer">' + history[current].plan + '</div>';
            document.getElementById("codeBlocks").appendChild(element)

            previousAgentResponse = ""
            let index = 0;
            for (const prompt of manager_plan) {
                index++;
                if(index === 1){
                    document.getElementById("1").style.backgroundColor = "#e37508";
                }else{
                    console.log((index-1).toString())
                    document.getElementById((index-1).toString()).style.backgroundColor = "#3b7c35";
                    document.getElementById((index).toString()).style.backgroundColor = "#e37508";
                }
                await agentTaskAPI(prevData, ("agent " + (index)), prompt, previousAgentResponse, index, JSON.stringify(data.CODE_FOUNDATION.ALL_CODE))
            }
            // Final Solution
            document.getElementById((index).toString()).style.backgroundColor = "#3b7c35";
            await getFinalSolution(prevData, previousAgentResponse, "");
        }
    }).catch(error =>{
        console.log(error)
        displayAlert("Manager Task API has failed" + error)
    })
}

let previousAgentResponse = "";
async function agentTaskAPI(prevFormData, agent, agentTask, agentResponses, index, code){
    prevFormData.append("agent_task", agentTask)
    prevFormData.append("agent_responses", agentResponses)
    prevFormData.append("code", code)

    await fetch("/Tasks/agent_task", {
        method: 'POST',
        body: prevFormData
    }).then(async response => {
        console.log(response)
        if (!response.ok) {
            displayAlert("Error on manager plan response")
        }
        const jsonResponse = await response.json();
        //Clear Response DIV
        document.getElementById("codeBlocks").innerHTML = "";
        // Create new element to display
        let element = document.createElement('div')
        element.className = "response";
        element.innerHTML =  '<div class="title">Agent ' + (index) +'</div>' + '<div class="agentAnswer '+ (index+1) + '">' + await jsonResponse + '</div>';
        document.getElementById("codeBlocks").appendChild(element)
        // Update current history
        console.log(index)
        history[current]["agent" + (index)] = jsonResponse;
        // Update Agent LOG
        previousAgentResponse = previousAgentResponse + "{" + jsonResponse + "}"
        return jsonResponse;
    }).catch(error =>{
        document.getElementById(index).style.background = "#a41c02";
        displayAlert("Agent Task has failed")
        return "Failed"
    })
}

async function getFinalSolution(prevFormData, code){
    document.getElementById("final").style.backgroundColor = "#e37508";
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
        try{
            if(data[0] && data.length < 200){
                //Clear Response DIV
                document.getElementById("codeBlocks").innerHTML = "";
                // Create new element to display
                let element = document.createElement('div')
                element.className = "response";
                element.innerHTML = ""
                for (const fileObject of data){
                    console.log("KEy")
                    console.log(fileObject)
                    // Update History
                    history[current].solution.push({
                        FILE_NAME: fileObject.FILE_NAME,
                        FILE_CODE: fileObject.FILE_CODE
                    })
                    element.innerHTML = element.innerHTML + '<div class="title">' + fileObject.FILE_NAME + '</div>' + '<div class="answer">' + fileObject.FILE_CODE + '</div>';
                    document.getElementById("codeBlocks").appendChild(element)
                }
                // Update History Perm
                console.log(history)
                localStorage.setItem("digitalHistory", JSON.stringify(history));
                document.getElementById("final").style.background = "#3b7c35";
            }else{
                document.getElementById("final").style.background = "#a41c02";
                //Clear Response DIV
                document.getElementById("codeBlocks").innerHTML = "";
                // Create new element to display
                let element = document.createElement('div')
                element.className = "response";
                element.innerHTML =  '<div class="title">' + 'Solution Failed To Parse' + '</div>' + '<div class="answer">' + JSON.stringify(data) + '</div>';
                document.getElementById("codeBlocks").appendChild(element)
            }

        }catch (e) {
            //Clear Response DIV
            document.getElementById("codeBlocks").innerHTML = "";
            // Create new element to display
            let element = document.createElement('div')
            element.className = "response";
            element.innerHTML =  '<div class="title">' + 'Solution Failed To Parse' + '</div>' + '<div class="answer">' + JSON.stringify(data) + '</div>';
            document.getElementById("codeBlocks").appendChild(element)
        }
    }).catch(error =>{
        displayAlert("Error on Final Solution")
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

const changeActive = (index) => {
    console.log(index)
    if(index !== -1){
        // Remove color
        document.getElementById("sesh" + active).style.backgroundColor = "#1f1f1f";
        // Highlight session
        document.getElementById("sesh"+index).style.backgroundColor = "#00477b"
        //Reset Colors
        active = index;
    }
    //Display Manager Plan
    document.getElementById("codeBlocks").innerHTML = "";
    // Create new session div
    let element = document.createElement('div')
    element.className = "response";
    element.innerHTML =  '<div class="title">Developer Plan</div>' + '<div class="agentAnswer">' + history[active].plan + '</div>';
    document.getElementById("codeBlocks").appendChild(element)
}

const loadSessions = () => {
    history.forEach(item => {
        let index = history.indexOf(item)
        let element = document.createElement('div')
        element.className = "session";
        element.id = "sesh" + index;
        element.innerText =  item.title;
        element.onclick = function(){changeActive(index)};
        document.getElementById("sessions").appendChild(element)
    })
}

const loadAgent = (agent, agentNumber) => {
    //Clear Response DIV
    document.getElementById("codeBlocks").innerHTML = "";
    // Create new element to display
    let element = document.createElement('div')
    element.className = "response";
    element.innerHTML =  '<div class="title">Agent ' + (agentNumber) +'</div>' + '<div class="agentAnswer '+ (agentNumber) + '">' + history[active][agent] + '</div>';
    document.getElementById("codeBlocks").appendChild(element)
}

const loadSolution = () => {
    //Clear Response DIV
    document.getElementById("codeBlocks").innerHTML = "";
    // Create new element to display
    let element = document.createElement('div')
    element.className = "response";
    element.innerHTML = "";

    history[active].solution.forEach(item => {
        element.innerHTML = element.innerHTML + '<div class="title">' + item.FILE_NAME + '</div>' + '<div class="answer">' + item.FILE_CODE + '</div>';
        document.getElementById("codeBlocks").appendChild(element)
    })
}

const clearHistory = () => {
    localStorage.removeItem("digitalHistory");
    history = [];
    //Clear Response DIV
    document.getElementById("codeBlocks").innerHTML = "";
    document.getElementById("sessions").innerHTML = '<h3>Sessions</h3>';
    resetColors();
}

const resetColors = () => {
    document.getElementById("1").style.backgroundColor = "#1f1f1f";
    document.getElementById("2").style.backgroundColor = "#1f1f1f";
    document.getElementById("3").style.backgroundColor = "#1f1f1f";
    document.getElementById("4").style.backgroundColor = "#1f1f1f";
    document.getElementById("5").style.backgroundColor = "#1f1f1f";
    document.getElementById("6").style.backgroundColor = "#1f1f1f";
    document.getElementById("final").style.backgroundColor = "#1f1f1f";
}

const hideRepo = () => {
    document.getElementById("repoSettings").style.display = "none";
}