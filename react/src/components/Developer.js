import {useEffect, useState} from "react";
import {agentTaskAPI, managerPlanAPI, repoOperationAPI, showDiff, solutionAPI} from "../api/Axios";
import {ReactComponent as ArrowIcon} from "../images/arrowIcon.svg"
import {ReactComponent as GitIcon} from "../images/gitIcon.svg";
import {ReactComponent as DiagramIcon} from "../images/flowChartIcon.svg";
import {ReactComponent as TrashIcon} from "../images/trashIcon.svg";
import DOMPurify from 'dompurify'
import parse, {attributesToProps} from "html-react-parser";

const Developer = () => {

    const options = {
        replace: domNode => {
            if(domNode.attribs && domNode.name === 'a'){
                const props = attributesToProps(domNode.attribs)
                let url = props['href']
                if(props && url){
                    let fullUrl = url.match(/^(https?)/g);
                    if(!fullUrl){
                        let newUrl = "//"+url
                        domNode.attribs = {...domNode.attribs, 'href':newUrl}
                    }
                }
            }
        }
    }

    const callParse = (txt) => {
        try{
            const purify = DOMPurify(window);
            let cleanHTMLTxt = purify.sanitize(txt);
            let parsed = parse(cleanHTMLTxt, options)
            return parsed
        }
        catch(error){
            return "error occured while parsing html. please try again"
        }
    }

    //Timer
    const [counter,setCounter] = useState(0)
    useEffect(() => {
        const timer = setInterval(()=>setCounter(counter + 1), 1000);
        return()=> clearInterval(timer);
    }, [counter]);

    const fillText = "<div class='introText'>\n\n\n" +
        "Repo Disclaimer: \n\n" +
        "For larger code repos it is recommended to be specific in your ask to avoid long wait times.\n\n" +
        "Recommended Examples:\n\n" +
        "Example 1:\n<div>Please optimize code in home.js for efficiency and precise code.\n</div>" +
        "Example 2:\n<div>For main.py, controller.py and service.py. implement multi-threading.\n</div>" +
        "</div>"


    //Get Local Storage History
    let hist = localStorage.getItem("digitalHistory") ? JSON.parse(localStorage.getItem("digitalHistory")) : [];
    //Session Object
    const [currentObject, setCurrentObject] = useState({})
    const [sessionIndex, setSessionIndex] = useState(-1)
    const [sessions, setSessions] = useState([])
    //variables input fields
    const [model, setModel] = useState(localStorage.getItem("model"))
    const [instruction, setInstruction] = useState("")
    const [file, setFile] = useState(null)
    const [gitRepo, setGitRepo] = useState("")
    const [currentBranch, setCurrentBranch] = useState("")
    const [newBranch, setNewBranch] = useState("")
    //Response Variables
    const [title, setTitle] = useState("Developer")
    const [task, setTask] = useState("")
    const [agentResponse, setAgentResponse] = useState(callParse(fillText))
    const [finalSolution, setFinalSolution] = useState([])
    //triggers
    const [showSettings, setShowSettings] = useState(false)
    const [solutionTrigger, setSolutionTrigger] = useState(false)
    const [showTabs, setShowTabs] = useState(false)
    const [running, setRunning] = useState(false)
    //Progress bar
    const [progress,setProgress] = useState({
        plan: "null",
        1: "null",
        2: "null",
        3: "null",
        4: "null",
        solution: "null",
        diff: "null"
    })

    const getBarClass = (item) => {
        if(progress[item] === "null"){
            return ""
        }
        if(progress[item] === "running"){
            return "progress-bar"
        }
        if(progress[item] === "complete"){
            return "progress-bar-complete"
        }
        if(progress[item] === "fail"){
            return "fail"
        }
    }
    //Main Flow Functions
    const handleSubmit = async () => {
        setModel(localStorage.getItem("model"))
        if(running === false){
            setProgress({
                plan: "null",
                1: "null",
                2: "null",
                3: "null",
                4: "null",
                solution: "null",
                diff: "null"
            });
            setTask("")
            setTitle("")
            setSessions(prevState => [...prevState, {id:hist.length, prompt: instruction}])
            setSessionIndex(hist.length)
            setRunning(true)
            setShowTabs(true)
            setSolutionTrigger(false)
            setFinalSolution([])
            let plan = {}
            //PROCESS FLOW
            if(gitRepo !== ""){
                setProgress(prevState => ({...prevState, plan:"running"}))
                let repoOps = await repoOperation()
                if(repoOps !== null && repoOps.files){
                    plan = await managerPlan(repoOps.files, repoOps.repo_dir)
                }
            }else{
                //no repo
                setNewBranch("none")
                plan = await managerPlan("none", "none")
            }
            let agents = plan !== null && plan.filenames !== null ? await processAgentTasks(plan.filenames ? plan.filenames : "", plan.repo_dir, plan.plan, plan.code) : [""]
            let solution = plan !== null && plan.filenames !== null ? await produceSolution(plan.filenames, plan.repo_dir, plan.code) : null

            let diff = ""
            if(gitRepo !== ""){
                diff = await executeChanges(plan.repo_dir, newBranch, solution)
            }

            setCurrentObject({
                id: hist.length,
                prompt: instruction,
                repo_dir: plan ? plan.repo_dir : "none",
                file_list: plan ? plan.file_list : "none",
                manager_plan: plan ? plan.plan : [],
                agentResponseList: agents,
                finalSolution: solution,
                diff: diff
            })
            hist.push({
                id: hist.length,
                prompt: instruction,
                repo_dir: plan ? plan.repo_dir : "none",
                file_list: plan ? plan.file_list : "none",
                manager_plan: plan ? plan.plan : [],
                agentResponseList: agents,
                finalSolution: solution,
                diff: diff
            })
            localStorage.setItem("digitalHistory", JSON.stringify(hist))
            setRunning(false)
            setFile(null)
        }
    }

    async function repoOperation(){
        return await repoOperationAPI(instruction, gitRepo, currentBranch, newBranch, localStorage.getItem("model"))
            .then((response)=>{
                return {repo_dir: response.data.repo_dir, files: response.data.files}
            }).catch((error)=>{
                setProgress(prevState => ({...prevState, plan:"fail"}))
                setAgentResponse("Branching Error, please try again or try different branch")
                return null
            })
    }

    async function managerPlan(file_list, repo_dir){
        setProgress(prevState => ({...prevState, plan:"running"}))
        return await managerPlanAPI(instruction,currentBranch,newBranch,localStorage.getItem("model"),file_list, repo_dir, file)
            .then((response)=> {
                if(file_list !== "none"){
                    setTitle("Manager Plan")
                    let managerPlanString = "";
                    response.data.forEach((item)=>{
                        managerPlanString = managerPlanString + "\nStep:\n" + item + "\n"
                    })
                    setAgentResponse("File List: " + file_list + "\n\n\nAgent Tasks: " + managerPlanString)
                    setProgress(prevState => ({...prevState, plan:"complete"}))

                    return {filenames: file_list, repo_dir: repo_dir, plan: response.data, code: null}
                }else{
                    setTitle("Manager Plan")
                    let managerPlanString = "";
                    response.data.MANAGER_PLAN.forEach((item)=>{
                        managerPlanString = managerPlanString + "\nStep:\n" + item + "\n"
                    })
                    setAgentResponse("\n\n\nAgent Tasks: " + managerPlanString + "\n\n CODE FOUNDATION:\n\n" + response.data.CODE_FOUNDATION.ALL_CODE)

                    setProgress(prevState => ({...prevState, plan:"complete"}))

                    let file_list = response?.data.CODE_FOUNDATION.FILE_NAMES
                    let plan = response?.data.MANAGER_PLAN
                    let code = response?.data.CODE_FOUNDATION.ALL_CODE

                    return {filenames: file_list, repo_dir: "none", plan: plan, code: code}
                }
            }).catch((err)=>{
                setProgress(prevState => ({...prevState, plan:"fail"}))
                return null
            })

    }

    let agentResponses = ""
    async function processAgentTasks(file_list, repo_dir, tasks, code=null){
        let agentResponseList = []
        try{
            for (const item of tasks){
                const index = tasks.indexOf(item);
                let response = await agentTask(index, file_list, newBranch, repo_dir, item, agentResponses, code)
                agentResponses = response
                agentResponseList.push(response)
            }
            return agentResponseList
        }catch(e){
            console.log(e)
            return []
        }
        async function agentTask(index, file_list, gitNewBranch, repo_dir, task, agent_responses, code){
            let agentNumber = index + 1;
            if(agentNumber === 1){
                setProgress(prevState => ({...prevState, 1:"running"}))
            }else if(agentNumber === 2){
                setProgress(prevState => ({...prevState, 2:"running"}))
            }
            else if(agentNumber === 3){
                setProgress(prevState => ({...prevState, 3:"running"}))
            }
            else if(agentNumber === 4){
                setProgress(prevState => ({...prevState, 4:"running"}))
            }
            return await agentTaskAPI(instruction,file_list,task, newBranch, repo_dir, agent_responses, code, localStorage.getItem("model"))
                .then((response) => {
                    if(agentNumber === 1){
                        setProgress(prevState => ({...prevState, 1:"complete"}))
                    }else if(agentNumber === 2){
                        setProgress(prevState => ({...prevState, 2:"complete"}))
                    }
                    else if(agentNumber === 3){
                        setProgress(prevState => ({...prevState, 3:"complete"}))
                    }
                    else if(agentNumber === 4){
                        setProgress(prevState => ({...prevState, 4:"complete"}))
                    }
                    setTitle("Agent " + agentNumber)
                    setTask(task)
                    if(repo_dir !== "none"){
                        setAgentResponse(response.data.agent_response)
                        agent_responses = response.data.agent_response
                        return response.data.agent_response
                    }else{
                        setAgentResponse(response.data.agent_response)
                        agent_responses = response.data.agent_response
                        return response.data.agent_response
                    }
                }).catch((err)=>{
                    if(agentNumber === 1){
                        setProgress(prevState => ({...prevState, 1:"fail"}))
                    }else if(agentNumber === 2){
                        setProgress(prevState => ({...prevState, 2:"fail"}))
                    }
                    else if(agentNumber === 3){
                        setProgress(prevState => ({...prevState, 3:"fail"}))
                    }
                    else if(agentNumber === 4){
                        setProgress(prevState => ({...prevState, 4:"fail"}))
                    }
                    return "NA"
                })
        }
    }

    async function produceSolution(file_list, repo_dir, code){
        setProgress(prevState => ({...prevState, solution:"running"}))
        return await solutionAPI(instruction, file_list, newBranch, repo_dir, agentResponses, code, localStorage.getItem("model"))
            .then((response)=>{
                setTitle("Final Solution")
                setTask("")
                if(response.data[0] && response.data[0].FILE_NAME){
                    setProgress(prevState => ({...prevState, solution:"complete"}))
                    setFinalSolution(response.data)
                    setSolutionTrigger(true);
                }else{
                    setProgress(prevState => ({...prevState, solution:"fail"}))
                    setAgentResponse(response.data)
                }
                return response.data
            }).catch((err)=>{
                setRunning(false)
                setProgress(prevState => ({...prevState, solution:"fail"}))
            })
    }

    async function executeChanges(repo_dir, newBranch, solution){
        setProgress(prevState => ({...prevState, diff:"running"}))
        return await showDiff(repo_dir, solution)
            .then((response)=>{
                setProgress(prevState => ({...prevState, diff:"complete"}))
                setTitle("GIT DIFF +/-")
                setAgentResponse(callParse(response.data))
                setSolutionTrigger(false)
                return response.data
            }).catch((err)=>{
                setProgress(prevState => ({...prevState, diff:"fail"}))
                return "null"
            })
    }

    //END OF MAIN FLOW FUNCTIONS
    //UTILITY FUNCTIONS
    const clearHistory = () => {
        setShowTabs(false)
        setSessionIndex(-1) //current
        setSolutionTrigger(false)
        setTask("")
        setTitle("")
        setAgentResponse("")
        setFinalSolution([])
        setSessions([])
        setInstruction("")
        setGitRepo("")
        setCurrentBranch("")
        setNewBranch("")
        setCurrentObject({})
        hist = []
        localStorage.removeItem("digitalHistory")
    }

    useEffect(() => {
        getAllSessions()
    }, []);

    const showPlan = () => {
        if(running !== true){
            setTitle("Manager Plan")
            let managerPlanString = "";
            currentObject.manager_plan.forEach((item)=>{
                managerPlanString = managerPlanString + "\nStep:\n" + item + "\n"
            })
            setAgentResponse("\n\n\nAgent Tasks: " + managerPlanString)
            setSolutionTrigger(false)
        }
    }
    const showAgent = (index) => {
        if(running !== true){
            setTitle("Agent " + (index+1))
            currentObject.agentResponseList[index] ? setAgentResponse(currentObject.agentResponseList[index]) : setAgentResponse("No Changes")
            setSolutionTrigger(false)
        }
    }
    const showSolution = () => {
        if(running !== true){
            setTitle("Final Solution")
            setTask("")
            if(currentObject.finalSolution && currentObject.finalSolution[0].FILE_NAME){
                console.log(currentObject.finalSolution)
                currentObject.finalSolution && currentObject.finalSolution[0].FILE_NAME ? setFinalSolution(currentObject.finalSolution) : setFinalSolution([])
                setSolutionTrigger(true)
            }else{
                setAgentResponse(currentObject.finalSolution)
            }
        }
    }

    const showGitDiff = () => {
        if(running !== true){
            let mainString = currentObject.diff !== null ? currentObject.diff : ""
            setTitle("Git Repo Differences")
            setAgentResponse(callParse(mainString))
            setSolutionTrigger(false)
        }
    }
    const getAllSessions = () => {
        let sessionList = []
        if(hist.length >= 1){
            hist.map((item) => {
                sessionList.push({id:item.id, prompt: item.prompt})
            })
            setSessions(sessionList)
        }
    }

    const selectSession = (index) => {
        if(running === false){
            setShowTabs(true)
            setSessionIndex(index)
            setCurrentObject(hist[index])
        }
    }



    const getSolutionDivs = (name, response) => {
        return (
            <div>
                <div className="fileName">{name}</div>
                <div className="fileCode">{response}</div>
            </div>
        )
    }

    const toggleDarkMode = () => {
        document.body.classList.toggle("darkMode");
    }

    const imageUpload = (e) => {
        setFile(e.target.files[0])
    }

    return (
        <div className="mainContainer">
            <div className="view">
                {showTabs &&
                    <div className="tabPanels">
                        <div className="agentTab">
                            <div disabled={running === true} onClick={() => {
                                showPlan()
                            }} id="planTab" className={`title ${getBarClass("plan")}`}>Plan
                            </div>
                        </div>
                        <div className="agentTab">
                            <div className={`title ${getBarClass("1")}`} id="agent0Tab" onClick={() => {
                                showAgent(0)
                            }}>Agent 1
                            </div>
                        </div>
                        <div className="agentTab">
                            <div className={`title ${getBarClass("2")}`} id="agent1Tab" onClick={() => {
                                showAgent(1)
                            }}>Agent 2
                            </div>
                        </div>
                        <div className="agentTab">
                            <div className={`title ${getBarClass("3")}`} id="agent2Tab" onClick={() => {
                                showAgent(2)
                            }}>Agent 3
                            </div>
                        </div>
                        <div className="agentTab">
                            <div className={`title ${getBarClass("4")}`} id="agent3Tab" onClick={() => {
                                showAgent(3)
                            }}>Agent 4
                            </div>
                        </div>
                        <div className="agentTab">
                            <div id="planTab" className={`title ${getBarClass("solution")}`} onClick={() => {
                                showSolution()
                            }}>Solution
                            </div>
                        </div>
                        <div className="agentTab">
                            <div id="planTab" className={`title ${getBarClass("diff")}`} onClick={() => {
                                showGitDiff()
                            }}>Diff
                            </div>
                        </div>
                    </div>
                }
                {
                    !solutionTrigger ?
                        <div className="agentResponse">
                            <h4 className="agentTitle">{title}</h4>
                            <h4 className="agentTitle">{task}</h4>
                            <div className="agentOutput">{agentResponse}</div>
                        </div>
                        :
                        <div className="agentResponse">
                            <h3 className="agentTitle">{title}</h3>
                            <h4 className="agentTitle">{task}</h4>
                            <div className="agentOutput">
                                {finalSolution.map((item, index) => (
                                    <div key={"sol" + index} className="output2">
                                        {getSolutionDivs(item.FILE_NAME ? item.FILE_NAME : "", item.FILE_CODE ? item.FILE_CODE : "")}
                                    </div>
                                ))}
                            </div>
                        </div>
                }
                <div className="promptContainer">
                    <button className="repoSettingsButton" onClick={() => {
                        setShowSettings(!showSettings)
                    }}><GitIcon className="img"/></button>
                    <label>
                        <input id="instruction" value={instruction} onChange={(e) => {
                            setInstruction(e.target.value)
                        }} type="text" title="instructions" placeholder="Enter Coding Instructions"/>
                    </label>
                    <label className="diagramImage">
                        <DiagramIcon className="img"/>
                        <input id="image" type="file" accept="image/png, image/gif, image/jpeg" onClick={(e) => {
                            e.target.value = ""
                        }} onChange={(e) => {
                            imageUpload(e)
                        }}/>
                    </label>
                    <button className="searchImage" onClick={() => {
                        handleSubmit()
                    }}><ArrowIcon className="img"/></button>
                </div>
            </div>
            {
                !showSettings ? <></> :
                    <div className="repoSettingsPopup">
                        <div className="repoContent">
                            <div>GIT REPO LINK</div>
                            <input id="cloneLInk" value={gitRepo} onChange={(e) => {
                                setGitRepo(e.target.value)
                            }} type="text" title="GIT CLONE LINK" placeholder="Enter HTTP Git Clone Link here"/>
                            <div>Branch Name</div>
                            <input id="branchName" value={currentBranch} onChange={(e) => {
                                setCurrentBranch(e.target.value)
                            }} type="text" title="Current Branch" placeholder="Enter Current Branch name here"/>
                            <div>New Branch Name</div>
                            <input id="newBranchName" value={newBranch} onChange={(e) => {
                                setNewBranch(e.target.value)
                            }} type="text" title="GIT CLONE LINK" placeholder="Enter New Branch name here"/>
                            <button className="repoSettingsButton" onClick={() => {
                                setShowSettings(false)
                            }}>Continue
                            </button>
                        </div>
                    </div>
            }
            <div className="menu">
                <div className="titleSessions">
                    Sessions
                </div>
                <div className="panel">
                    <span className="clear" onClick={() => {
                        clearHistory()
                    }}><TrashIcon className="img" title="Clear History"/></span>
                    <div className="panelContainer">
                        {sessions.map((item, index) => (
                            <div disabled={running === true} key={index}
                                 className={`session ${index === sessionIndex ? "activeSession" : ""}`} onClick={() => {
                                selectSession(index)
                            }}>
                                {item.prompt}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Developer;