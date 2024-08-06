let history = localStorage.getItem("digitalHistory")
    ? JSON.parse(localStorage.getItem("digitalHistory"))
    : [];
let active = -1;
let current = -1;
let repo = false;
let running = false;
let activeList = [];
let activeRepo = [];
let model = "oai";

window.onload = function () {
    hideAll();
    loadSessions()
}

function toggleModel(){
    if(model === "oai"){
        model = "elf"
        document.getElementById('switch').innerText = "ELF"
    }else{
        model = "oai"
        document.getElementById('switch').innerText = "OAI"
    }
}

function showRepoSettings(){
    document.getElementById("repoSettings").style.display = "block";
}

function flowChecker(){
    hideAll();
    let repoInput = document.getElementById("repo").value;
    if(repoInput === ""){
        repo = false;

        current = history.length;
        // new history object
        let object = {
            "title": document.getElementById("instruction").value,
            "plan": "loader",
            "agent1": "loader",
            "agent2": "loader",
            "agent3": "loader",
            "agent4": "loader",
            "solution": [],
            "repo_dir": null,
            "differences": ""
        }
        history.push(object)

        // Create new session div
        let element = document.createElement('div')
        element.className = "session";
        element.innerText =  document.getElementById("instruction").value;
        element.id = "sesh" + current;
        element.onclick = function(){changeActive(current)};
        document.getElementById("sessions").appendChild(element)

        changeActive(current);
        running = true;

        // Empty Response Div
        document.getElementById("codeBlocks").innerHTML = ""

        //Create Base formdata
        let formData = new FormData();
        if($("#image")[0].files[0]){
            formData.append("file", $("#image")[0].files[0]);
        }
        formData.append("user_prompt", document.getElementById("instruction").value);
        formData.append("https_clone_link", "none");
        formData.append("original_code_branch", "none");
        formData.append("new_branch_name", "none");
        formData.append("flow", "no")
        formData.append("model", model)
        // Call Manager API
        managerTasksAPI(formData,"none","none")
    }else{
        repo = true;
        digitalAgentAPI()
    }
}

function digitalAgentAPI(){
    let formData = new FormData();
    let instruction = document.getElementById("instruction").value;
    formData.append("user_prompt", instruction);
    formData.append("https_clone_link", document.getElementById("repo").value);
    formData.append("original_code_branch", document.getElementById("branch").value);
    formData.append("new_branch_name", document.getElementById("newBranch").value);
    formData.append("flow", "no")
    formData.append("model", model)

    // Call API
    fetch("/Tasks/repo_ops", {
        method: 'POST',
        body: formData
    }).then(response => {
        console.log(response)
        if(!response.ok){
            running = false;
            displayAlert("Error on clone response")
        }
        return response.json();
    }).then(data => {
        current = history.length;
        // new history object
        let object = {
            "title": instruction,
            "plan": "loader",
            "agent1": "loader",
            "agent2": "loader",
            "agent3": "loader",
            "agent4": "loader",
            "solution": [],
            "repo_dir": data.repo_dir,
            "big_repo": false,
            "differences": ""
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
        running = false;
        displayAlert("Git Repo Clone API Failed" + error)
    })
}

function managerTasksAPI(prevData, files, directory){
    document.getElementById("plan").className = "step";
    document.getElementById("progPlan").style.display = "block";
    document.getElementById("progressBarPlan").className = "progress-bar";

    prevData.append("file_list", files)
    prevData.append("repo_dir", directory)
    fetch("/Tasks/manager_plan", {
        method: 'POST',
        body: prevData
    }).then(response => {
        console.log(response)
        if(!response.ok){
            running = false;
            document.getElementById("progressBarPlan").className = "progress-bar3";
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
            document.getElementById("progressBarPlan").className = "progress-bar2";

            previousAgentResponse = ""
            let index = 0;
            for (const prompt of data) {
                index++;
                await agentTaskAPI(prevData, ("agent " + (index)), prompt, previousAgentResponse, index)
            }
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
            element.innerHTML =  '<div class="title">Developer Plan</div>' + '<div class="agentAnswer">' + history[current].plan + '\nCODE FOUNDATION\n' + data.CODE_FOUNDATION.ALL_CODE + '</div>';
            document.getElementById("codeBlocks").appendChild(element)
            document.getElementById("progressBarPlan").className = "progress-bar2";

            previousAgentResponse = ""
            let index = 0;
            for (const prompt of manager_plan) {
                index++;
                await agentTaskAPI(prevData, ("agent " + (index)), prompt, previousAgentResponse, index, JSON.stringify(data.CODE_FOUNDATION.ALL_CODE))
            }
            // Final Solution
            await getFinalSolution(prevData, previousAgentResponse, "");
        }
    }).catch(error =>{
        running = false;
        console.log(error)
        displayAlert("Manager Task API has failed" + error)
    })
}

let previousAgentResponse = "";
let prevAgentLists = []
async function agentTaskAPI(prevFormData, agent, agentTask, agentResponses, index, code){
    prevFormData.set("agent_task", agentTask)
    if(history[current].big_repo === true){
        prevFormData.set("agent_responses", JSON.stringify(prevAgentLists))
    }else{
        prevFormData.set("agent_responses", agentResponses)
    }
    prevFormData.set("code", code)

    document.getElementById(index.toString()).className = "step";
    document.getElementById("prog"+index).style.display = "block";
    document.getElementById("progressBar"+index).className = "progress-bar";

    await fetch("/Tasks/agent_task", {
        method: 'POST',
        body: prevFormData
    }).then(async response => {
        console.log(response)
        if (!response.ok) {
            displayAlert("Error on manager plan response")
            document.getElementById("progressBar"+index).className = "progress-bar3";
        }else{
            document.getElementById("progressBar"+index).className = "progress-bar2";
            const jsonResponse = await response.json();
            // Low Token Approach
            if(jsonResponse.agent_response){
                //Clear Response DIV
                document.getElementById("codeBlocks").innerHTML = "";
                // Create new element to display
                let element = document.createElement('div')
                element.className = "response";
                element.innerHTML =  '<div class="title">Agent ' + (index) +'</div>' + '<div class="agentAnswer '+ (index+1) + '">' + await jsonResponse.agent_response + '</div>';
                document.getElementById("codeBlocks").appendChild(element)
                // Update current history
                console.log(index)
                history[current]["agent" + (index)] = jsonResponse.agent_response;
                if(index === 4){
                    // Update Agent LOG
                    previousAgentResponse = "\"agent\" + (index)" + jsonResponse.agent_response + "}"
                }else{
                    // Update Agent LOG
                    previousAgentResponse = previousAgentResponse + "{" + jsonResponse.agent_response + "}"
                }
            }
            if(jsonResponse.agent_response_list){
                //Clear Response DIV
                document.getElementById("codeBlocks").innerHTML = "";
                let element = document.createElement('div')
                element.className = "response";
                element.innerHTML = ""
                for (const fileObject of jsonResponse.agent_response_list){
                    element.innerHTML = element.innerHTML + '<div class="title">' + fileObject.FILE_NAME + '</div>' + '<div class="answer">' + fileObject.FILE_CODE + '</div>';
                    document.getElementById("codeBlocks").appendChild(element)
                }
                // Update current history
                history[current]["agent" + (index)] = jsonResponse.agent_response_list;
                history[current].big_repo = true;
                if(index === 4){
                    // Update Agent LOG
                    prevAgentLists = jsonResponse.agent_response_list
                }else{
                    // Update Agent LOG
                    prevAgentLists = jsonResponse.agent_response_list
                }
            }
            return jsonResponse;
        }
    }).catch(error =>{
        document.getElementById("progressBar"+index).className = "progress-bar3";
        displayAlert("Agent Task has failed")
        return "Failed"
    })
}

async function getFinalSolution(prevFormData, code){
    $("#image").val(null)
    if(history[current].big_repo === true){
        prevFormData.set("agent_responses", JSON.stringify(prevAgentLists))
    }else{
        prevFormData.append("agent_responses", previousAgentResponse)
    }

    document.getElementById("final").className = "step";
    document.getElementById("progFinal").style.display = "block";
    document.getElementById("progressBarFinal").className = "progress-bar";
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
                document.getElementById("progressBarFinal").className = "progress-bar2";
                //Show Differences
                if(prevFormData.get("repo_dir") !== "none"){
                    displayDifferences(prevFormData.get("repo_dir"), data)
                }
            }else{
                document.getElementById("progressBarFinal").className = "progress-bar3";
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
            document.getElementById("progressBarFinal").className = "progress-bar3";
        }
    }).catch(error =>{
        displayAlert("Error on Final Solution")
    })
    running = false;
}


async function displayDifferences(repo_dir, code){

    document.getElementById("differences").className = "step";
    document.getElementById("progDifferences").style.display = "block";
    document.getElementById("progressBarDifferences").className = "progress-bar";

    await fetch("/Tasks/show_diff", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({"repo_dir": repo_dir, "produced_code": code})
    }).then(async response => {
        console.log(response)
        if (!response.ok) {
            displayAlert("Error on Comparison")
            document.getElementById("progressBarDifferences").className = "progress-bar3";
        }else{
            document.getElementById("progressBarDifferences").className = "progress-bar2";
            const jsonResponse = await response.json();
            console.log(jsonResponse)
            history[current].differences = await jsonResponse;
            localStorage.setItem("digitalHistory", JSON.stringify(history));
            //Clear Response DIV
            document.getElementById("codeBlocks").innerHTML = "";
            // Create new element to display
            let element = document.createElement('div')
            element.className = "response";
            element.innerHTML =  '<div class="title">Code Comparison ' + '</div>' + '<div class="agentAnswer">' + await jsonResponse + '</div>';
            document.getElementById("codeBlocks").appendChild(element)
        }
    }).catch(error =>{
        document.getElementById("progressBarDifferences").className = "progress-bar3";
        displayAlert("Compare Task has failed")
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


const changeToPlan = () => {
    //Display Manager Plan
    document.getElementById("codeBlocks").innerHTML = "";
    // Create new session div
    let element = document.createElement('div');
    element.className = "response";
    element.innerHTML =  '<div class="title">Developer Plan</div>' + '<div class="agentAnswer">' + history[active].plan + '</div>';
    document.getElementById("codeBlocks").appendChild(element);
}

const changeActive = (index) => {
    console.log(running)
    console.log(index)
    if(running === false){
        if(index !== -1){
            // Remove color
            if(active !== -1){
                document.getElementById("sesh" + active).className = "session";
            }
            // Highlight session
            document.getElementById("sesh"+index).className = "activeSession";
            //Reset Colors
            active = index;

            if(active !== current){
                //Show all bars
                showAll();
            }
        }
    }
    if(running === true && index === current){
        // Remove color
        if(active !== -1){
            document.getElementById("sesh" + active).className = "session";
        }
        // Highlight session
        document.getElementById("sesh"+index).className = "activeSession";
        //Reset Colors
        active = index;
    }
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
    if(running !== true){
        //Clear Response DIV
        document.getElementById("codeBlocks").innerHTML = "";
        // Create new element to display
        let element = document.createElement('div')
        element.className = "response";
        if(!Array.isArray(history[active][agent])){
            element.innerHTML =  '<div class="title">Agent ' + (agentNumber) +'</div>' + '<div class="agentAnswer '+ (agentNumber) + '">' + history[active][agent] + '</div>';
            document.getElementById("codeBlocks").appendChild(element)
        }else{
            element.innerHTML = ""
            for (const fileObject of history[active][agent]){
                element.innerHTML = element.innerHTML + '<div class="title">' + fileObject.FILE_NAME + '</div>' + '<div class="answer">' + fileObject.FILE_CODE + '</div>';
                document.getElementById("codeBlocks").appendChild(element)
            }
        }
    }
}

const loadSolution = () => {
    if(running !== true){
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
}

const clearHistory = () => {
    localStorage.removeItem("digitalHistory");
    history = [];
    hideAll();
    //Clear Response DIV
    document.getElementById("codeBlocks").innerHTML = "";
    document.getElementById("sessions").innerHTML = '<h3>Sessions</h3>';
    // Clear All Input Values
    document.getElementById("instruction").value = "";
    document.getElementById("repo").value = "";
    document.getElementById("branch").value = "";
    document.getElementById("newBranch").value = "";
    $("#image").val(null)
}

const hideAll = () => {
    document.getElementById("plan").className = "hideStep";
    document.getElementById("1").className = "hideStep";
    document.getElementById("2").className = "hideStep";
    document.getElementById("3").className = "hideStep";
    document.getElementById("4").className = "hideStep";
    document.getElementById("final").className = "hideStep";
    document.getElementById("differences").className = "hideStep";
    document.getElementById("progPlan").style.display = "none";
    document.getElementById("prog1").style.display = "none";
    document.getElementById("prog2").style.display = "none";
    document.getElementById("prog3").style.display = "none";
    document.getElementById("prog4").style.display = "none";
    document.getElementById("progFinal").style.display = "none";
    document.getElementById("progDifferences").style.display = "none";
}
const showAll = () => {
    document.getElementById("plan").className = "step";
    document.getElementById("1").className = "step";
    document.getElementById("2").className = "step";
    document.getElementById("3").className = "step";
    document.getElementById("4").className = "step";
    document.getElementById("final").className = "step";
    document.getElementById("differences").className = "step";
    document.getElementById("progPlan").style.display = "block";
    document.getElementById("prog1").style.display = "block";
    document.getElementById("prog2").style.display = "block";
    document.getElementById("prog3").style.display = "block";
    document.getElementById("prog4").style.display = "block";
    document.getElementById("progFinal").style.display = "block";
    document.getElementById("progDifferences").style.display = "block";
}

const hideRepo = () => {
    document.getElementById("repoSettings").style.display = "none";
}

const toggleLightDarkMode = () => {
    document.body.classList.toggle("darkModeBoth");
}

const showDifferences = () => {
    document.getElementById("codeBlocks").innerHTML = "";
    // Create new element to display
    let element = document.createElement('div')
    element.className = "response";
    element.innerHTML =  '<div class="title">Code Comparison ' + '</div>' + '<div class="agentAnswer">' + history[active].differences + '</div>';
    document.getElementById("codeBlocks").appendChild(element);
}