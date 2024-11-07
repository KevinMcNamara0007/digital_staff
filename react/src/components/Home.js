import {useEffect, useRef, useState} from "react";
import {
    classify,
    classifyRepoRequired,
    executePlanPrompt,
    getRepoDetails,
    dataGenerate,
    askLLM, askDifferentlyPrompt
} from "./constants/constants";
import TableData from "./TableData";
import {Button} from "react-bootstrap";
import {ReactComponent as CheckIcon} from "../images/check.svg"
import {ReactComponent as SendIcon} from "../images/send.svg"

const Home = () => {
    const [dropdownOpen, setDropdownOpen] = useState(false);
    const [toggleModel, setToggleModel] = useState("elf")
    const [showAllTables, setShowAllTables] = useState(false)
    const [loader, setLoader] = useState(false)
    const [running, setRunning] = useState(false)
    const [instruction, setInstruction] = useState("")
    const [repo, setRepo] = useState({required:"",repoLink:"",branch:"", newBranch:"",allCode:"",dir:"",lastResponse:"",files:""})
    const [dataDetails, setDataDetails] = useState({description:"", rows:"",input:"", label:"", data:[], count:0})
    const [persona, setPersona] = useState("Persona")
    const [messages, setMessages] = useState([
        { type: 'assistant', text: 'Hello! How can I help you today?' },
        { type: 'assistant', text: 'Example: "Write me the game of snake in python"' },
        { type: 'assistant', text: 'Example: "In my Repo, please implement multi-threading where applicable"'},
        { type: 'assistant', text: 'Example: "Create a data annotation contract"'},
    ]);
    const chatInputRef = useRef(null);
    const messagesEndRef = useRef(null);

    const handleInput = () => {
        const chatInput = chatInputRef.current;
        if (chatInput) {
            chatInput.style.height = 'auto'; // Reset height so it can shrink on deletion
            chatInput.style.height = `${chatInput.scrollHeight}px`; // Set height based on content
        }
    };

    const handleKeyDown = async (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            await handleSendMessage();
        }
    };

    const handleAttachment = (event) => {
        const file = event.target.files[0];
        if (file) {
            setMessages([...messages, { type: 'user', text: `Attached: ${file.name}` }]);
        }
    };
    const handleSendMessage = async () => {
        const message = chatInputRef.current.value.trim();
        if (message !== '') {
            setMessages([...messages, { type: 'user', text: message }]);
            chatInputRef.current.value = '';
            handleInput(); // Reset the height after sending the message
        }

        if (!running) {
            setInstruction(message)
            await handleFlow(message);
        } else if (persona === 'Developer') {
            await developerFlow(message)
        } else if (persona === 'Data'){
            await dataFlow(message)
        }


    };

    const dataFlow = async (message) => {
        let object = {description:"", rows:"",input:"", label:""}
        if(!dataDetails.description){
            setDataDetails(prevState => ({...prevState, description: message}))
            setMessages((prevMessages) => [
                ...prevMessages,
                {type: 'assistant', text: 'How many records(rows) would you like to make? Pick from 1-100'}
            ]);
        } else if(!dataDetails.rows){
            try{
                let records = parseInt(message)
                console.log(records)
                if(records < 100){
                    setDataDetails(prevState => ({...prevState, rows: records}))
                    setMessages((prevMessages) => [
                        ...prevMessages,
                        {type: 'assistant', text: 'What would you like your input to be?\nExample: Technology Help Desk Tickets 100 words or less.'}
                    ]);
                }else{
                    setDataDetails(prevState => ({...prevState, rows: 50}))
                    setMessages((prevMessages) => [
                        ...prevMessages,
                        {type: 'assistant', text: 'What would you like your input to be?\nExample: Technology Help Desk Tickets 100 words or less.'}
                    ]);
                }
            }catch(e){
                setMessages((prevMessages) => [
                    ...prevMessages,
                    {type: 'assistant', text: 'Please enter a number from 1-100 only.'}
                ]);
            }
        } else if(!dataDetails.input){
            setDataDetails(prevState => ({...prevState, input: message}))
            setMessages((prevMessages) => [
                ...prevMessages,
                {type: 'assistant', text: 'What would you like to label?\nExample: Classification from low, medium or high priority.'}
            ]);
        } else if(!dataDetails.label){
            setDataDetails(prevState => ({...prevState, label: message}))
            setMessages((prevMessages) => [
                ...prevMessages,
                {type: 'assistant', text: 'Is this data contract correct?\n' +
                        'Annotation Name: ' + dataDetails.description + '\n' +
                        'Records: ' + dataDetails.rows + '\n' +
                        'Input: ' + dataDetails.input + '\n' +
                        'Label: ' + message
                }
            ]);
        } else{
            if (message.toLowerCase().includes("yes") || !message.toLowerCase().includes("no")) {
                await handleFlow(instruction)
            }else{
                setDataDetails({description:"", rows:"",input:"", label:""})
                setMessages((prevMessages) => [
                    ...prevMessages,
                    {type: 'assistant', text: 'Okay, lets correct this information.'},
                    {type: 'assistant', text: 'Please provide your GitHub HTTPS Clone Link.'}
                ]);
            }
        }

    }

    const developerFlow = async (message) => {
        if (!repo.repoLink) {
            setRepo((prevState) => ({...prevState, repoLink: message}));
            setMessages((prevMessages) => [
                ...prevMessages,
                {type: 'assistant', text: 'Please provide your Project Branch Name.'}
            ]);
        } else if (!repo.branch) {
            setRepo((prevState) => ({...prevState, branch: message}));
            setMessages((prevMessages) => [
                ...prevMessages,
                {type: 'assistant', text: 'Please provide a new branch name for me to push to.'}
            ]);
        } else if (!repo.newBranch) {
            setRepo((prevState) => ({...prevState, newBranch: message}));
            setMessages((prevMessages) => [
                ...prevMessages,
                {
                    type: 'assistant',
                    text: 'Is this information correct?\nHTTP LINK: ' + repo.repoLink + "\nCurrent Branch: " + repo.branch + "\nNew Branch: " + message
                }
            ]);
        } else {
            if (message.toLowerCase().includes("yes")) {
                await handleFlow(instruction)
            } else {
                setRepo({required: "yes", repoLink: "", branch: "", newBranch: ""})
                setMessages((prevMessages) => [
                    ...prevMessages,
                    {type: 'assistant', text: 'Okay, lets get the correct information.'},
                    {type: 'assistant', text: 'Give me a brief description or name about the data contract you want to create.'}
                ]);

            }
        }
    }

    const handleFlow = async (input) => {
        setLoader(true)
        let personaClassification = persona
        let repoRequired = repo.required
        if (!running && personaClassification === "Persona") {
            personaClassification = await classify(input);
            setPersona(personaClassification);
            setRunning(true);
        }

        if (personaClassification === 'General') {
            await callAPI(input);
            setRunning(false);
        } else if (personaClassification === 'Developer') {
            if (repoRequired === "") {
                console.log("got to classify")
                repoRequired = await classifyRepoRequired(input);
                setRepo((prevState) => ({ ...prevState, required: repoRequired }));
            }
            console.log(repoRequired)
            if(repoRequired === "yes"){
                if (repo.repoLink === "") {
                    setMessages((prevMessages) => [
                        ...prevMessages,
                        { type: 'assistant', text: 'Please provide your GitHub HTTP Clone Link.' }
                    ]);
                }
                if(repo.repoLink && repo.branch && repo.newBranch){
                    console.log(repo)
                    let code = repo.allCode
                    if(repo.dir === ""){
                        let codeData = await getRepoDetails(instruction, repo.repoLink, repo.branch, repo.newBranch)
                        setRepo((prevState) => ({ ...prevState, dir: codeData.repo_dir, files: codeData.files, allCode: codeData.all_code }));
                        code = codeData.all_code
                    }
                    console.log("here")
                    let solution = await callAPI(executePlanPrompt(instruction, code))
                    console.log(solution[solution.length - 1].text)
                    setRunning(false)

                }
            }
            if (repoRequired === 'no') {
                let response = await callAPI(input);
                setRunning(false);
            }
        } else if(personaClassification === "Data"){
            if(dataDetails.description === ""){
                let agentText = await askLLM(askDifferentlyPrompt("Give me a brief description or name about the data contract you want to create."))
                setMessages((prevMessages) => [
                    ...prevMessages,
                    { type: 'assistant', text: agentText ? agentText : 'We will be setting up your data annotation contract.\n Give me a brief description or name about the data contract you want to create.' }
                ]);
            }
            if(dataDetails.description && dataDetails.rows && dataDetails.input && dataDetails.label){
                let tableData = await dataGenerate(dataDetails.description, dataDetails.rows, dataDetails.input, dataDetails.label)
                setDataDetails(prevState => ({...prevState, data: prevState.data.concat(tableData), count: prevState.count+1}))
                let agentText = await askLLM(askDifferentlyPrompt("Here is your Complete Data Contract."))
                setMessages((prevMessages) => [
                    ...prevMessages,
                    { type: 'assistant', text: agentText ? agentText : 'Here is your Complete Contract.',  data:true, array:tableData, count:dataDetails.count+1}
                ]);

            }
        }

        setLoader(false)
    };

    async function callAPI(prompt) {
        let text = ""
        // Add a new empty assistant message to start updating with streamed chunks
        setMessages((prevMessages) => [
            ...prevMessages,
            { type: 'assistant', text: "" }
        ]);

        try {
            const response = await fetch("http://192.168.1.13:8000/Inference/ask_a_pro_stream", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'token': 'fja0w3fj039jwiej092j0j-9ajw-3j-a9j-ea'
                },
                body: JSON.stringify({ "output_tokens": 12000, "prompt": prompt })
            });

            if (!response.ok) {
                throw new Error(`Error: ${response.status} - ${response.statusText}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const textChunk = decoder.decode(value, { stream: true });

                // Update only the last message dynamically by appending the streamed text chunk
                setMessages((prevMessages) => {
                    const updatedMessages = [...prevMessages];

                    // Avoid duplications by only updating the last assistant message
                    updatedMessages[updatedMessages.length - 1] = {
                        ...updatedMessages[updatedMessages.length - 1],
                        text: updatedMessages[updatedMessages.length - 1].text + textChunk
                    };
                    text = updatedMessages;
                    return updatedMessages;
                });
            }
            return text
        } catch (error) {
            console.error('API call failed:', error);
        }
    }

    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);

    const clearHistory = () => {
        setShowAllTables(false)
        setLoader(false)
        setRunning(false)
        setInstruction("")
        setRepo({required:"",repoLink:"",branch:"", newBranch:"",allCode:"",dir:"",lastResponse:"",files:""})
        setDataDetails({description:"", rows:"",input:"", label:"", data:[], count:0})
        setPersona("Persona")
        setMessages([
            { type: 'assistant', text: 'Hello! How can I help you today?' }
        ]);
    }

    return (
        <div className="chat-container">
            <div className="chat-header">
                <div
                    className="persona-dropdown-container"
                    data-arrow={dropdownOpen ? "▲" : "▼"} // Toggle arrow icon
                    onFocus={() => setDropdownOpen(true)}
                    onBlur={() => setDropdownOpen(false)}
                >
                    <select
                        className="persona-dropdown"
                        value={persona}
                        onChange={(e) => setPersona(e.target.value)}
                    >
                        <option value="Persona">Persona</option>
                        <option value="General">General</option>
                        <option value="Developer">Developer</option>
                        <option value="Data">Data</option>
                        <option value="Content">Content</option>
                    </select>
                </div>
                <span className="title">eStaff</span>
                <label className="switch">
                    <input type="checkbox"/>
                    <div className="slider slider--0" onClick={() => {
                        setToggleModel("oai")
                    }}>ELF
                    </div>
                    <div className="slider slider--1">
                        <div></div>
                        <div></div>
                    </div>
                    <div className="slider slider--2"></div>
                    <div className="slider slider--3" onClick={() => {
                        setToggleModel("elf")
                    }}>OAI
                    </div>
                </label>
            </div>
            <div className="chat-messages">
                {messages.map((msg, index) => (
                    <div
                        key={index}
                        className={`chat-message ${msg.type === 'user' ? 'user-message' : 'assistant-message'}`}
                    >
                        {msg.text}
                        {msg.data && msg.data === true && dataDetails.data.length > 1 &&
                            <div>
                                {showAllTables ? <TableData data={dataDetails.data}/> : <TableData data={msg.array}/>}
                                <CheckIcon title="Finished" className="icon float-end"/>
                                {dataDetails.count > 1 && msg.count > 1 &&
                                    <Button variant="success" className="" onClick={()=>{setShowAllTables(!showAllTables)}}>{showAllTables ? "go back" : "Combine Previous"}</Button>
                                }
                            </div>
                        }
                    </div>
                ))}
                {loader &&
                    <div className="chat-message assistant-message">
                        <div className="loader">
                            <div className="loader__circle"></div>
                            <div className="loader__circle"></div>
                            <div className="loader__circle"></div>
                        </div>
                    </div>
                }
                <div ref={messagesEndRef}/>
            </div>
            <div className="chat-input-area">
                <textarea
                    ref={chatInputRef}
                    className="chat-input"
                    placeholder="Type a message..."
                    onKeyDown={handleKeyDown}
                    onInput={handleInput}
                ></textarea>
                <button className="send-button" onClick={handleSendMessage}>
                    <SendIcon className="icon"/>
                </button>
                <div>
                    <label className="attachment-label" htmlFor="attachment">
                        Upload
                    </label>
                    <input
                        type="file"
                        id="attachment"
                        className="attachment-input"
                        onChange={handleAttachment}
                        accept="image/*"
                    />
                    <label className="attachment-label" onClick={()=>{clearHistory()}}>
                        Clear History
                    </label>
                </div>
            </div>
        </div>
    );
};

export default Home;
