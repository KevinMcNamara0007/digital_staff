import {useEffect, useRef, useState} from "react";
import {
    classify,
    classifyRepoRequired,
    executePlanPrompt,
    getRepoDetails,
    dataGenerate,
    askLLM,
    askDifferentlyPrompt,
    createNewFiles,
    getGitChanges,
    getContentReviewPrompt,
    finalDraftPrompt,
    executePlanWithResponsePrompt
} from "./constants/constants";
import TableData from "./TableData";
import {Button} from "react-bootstrap";
import {ReactComponent as CheckIcon} from "../images/check.svg"
import {ReactComponent as SendIcon} from "../images/send.svg"
import {ReactComponent as DiffIcon} from "../images/diff.svg"
import parse, {attributesToProps} from "html-react-parser";
import DOMPurify from "dompurify";

const Home = () => {
    const [showPlan, setShowPlan] = useState(false)
    const [lastResponse, setLastResponse] = useState("")
    const [dropdownOpen, setDropdownOpen] = useState(false);
    const [toggleModel, setToggleModel] = useState("oai")
    const [showAllTables, setShowAllTables] = useState(false)
    const [loader, setLoader] = useState(false)
    const [running, setRunning] = useState(false)
    const [instruction, setInstruction] = useState("")
    const [repo, setRepo] = useState({required:"",repoLink:"",branch:"", newBranch:"",allCode:"",dir:"",lastResponse:"",files:""})
    const [dataDetails, setDataDetails] = useState({description:"", rows:"",input:"", label:"", data:[], count:0})
    const [contentDetails, setContentDetails] = useState({description:"",style:"",tone:"", content:""})
    const [persona, setPersona] = useState("Persona")
    const [messages, setMessages] = useState([
        { type: 'assistant', text: 'Hello! How can I help you today?' },
        { type: 'assistant', text: 'Example: "Write me the game of snake in python"' },
        { type: 'assistant', text: 'Example: "In my Repo, please implement multi-threading where applicable"'},
        { type: 'assistant', text: 'Example: "Create a data annotation contract"'},
        { type: 'assistant', text: 'Example: "Review my Rough Draft for a Help Desk Article"'},
    ]);
    const chatInputRef = useRef(null);
    const messagesEndRef = useRef(null);

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

        if (running === false) {
            setInstruction(message)
            await handleFlow(message);
        } else if (persona === 'Developer') {
            await developerFlow(message)
        } else if (persona === 'Data'){
            await dataFlow(message)
        } else if (persona === 'Content'){
            await contentFlow(message)
        }


    };

    const contentFlow = async (message) => {
        if(!contentDetails.description){
            setContentDetails(prevState => ({...prevState, description:message}))
            setMessages((prevMessages) => [
                ...prevMessages,
                {type: 'assistant', text: 'Please Enter your content.'}
            ]);
        }else if(!contentDetails.content){
            setContentDetails(prevState => ({...prevState, content:message}))
            setMessages((prevMessages) => [
                ...prevMessages,
                {type: 'assistant', text: 'Why style would you like this in?\nEX: AP, Blog, MLA, CMS, AMA...'}
            ]);
        }else if(!contentDetails.style){
            setContentDetails(prevState => ({...prevState, style:message}))
            setMessages((prevMessages) => [
                ...prevMessages,
                {type: 'assistant', text: 'What type of tone would you like to give off?\nEX: Formal, Creative, Friendly, Funny...'}
            ]);
        }else if(!contentDetails.tone){
            setContentDetails(prevState => ({...prevState, tone:message}))
            setMessages((prevMessages) => [
                ...prevMessages,
                {type: 'assistant', text: 'Is this information correct?\nStyle: ' + contentDetails.style + "\nTone: " + message}
            ]);
        }else{
            if (message.toLowerCase().includes("yes") || !message.toLowerCase().includes("no")) {
                await handleFlow()
            }else{
                setContentDetails({description:"",style:"",tone:"", content:""})
                setMessages((prevMessages) => [
                    ...prevMessages,
                    {type: 'assistant', text: 'Okay, lets start from the beginning.\nWhat would you like to do with the content?'}
                ]);
            }
        }
    }

    const dataFlow = async (message) => {
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
                    text: 'Is this information correct?\nHTTPS LINK: ' + repo.repoLink + "\nCurrent Branch: " + repo.branch + "\nNew Branch: " + message
                }
            ]);
        } else {
            if (message.toLowerCase() !== "no") {
                if(lastResponse === ""){
                    await handleFlow(instruction)
                }else{
                    await handleFlow(message)
                }
            } else {
                setRepo({required: "yes", repoLink: "", branch: "", newBranch: ""})
                setMessages((prevMessages) => [
                    ...prevMessages,
                    {type: 'assistant', text: 'Okay, lets get the correct information.'},
                    {type: 'assistant', text: 'What is the correct GitHub HTTPS Clone Link?'}
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
                    let solution = ""
                    if(lastResponse === ""){
                        solution = await callAPI(executePlanPrompt(instruction, code),true)
                        setLastResponse(solution)
                    }else{
                        solution = await callAPI(executePlanWithResponsePrompt(input, code, lastResponse),true)
                        setLastResponse(solution)
                    }
                    setRepo((prevState) => ({ ...prevState, lastResponse: solution}));

                }
            }
            if (repoRequired === 'no') {
                // let plan = await callAPI("")
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
        } else if(personaClassification === "Content"){
            if(!contentDetails.description){
                setContentDetails(prevState => ({...prevState, description: input}))
                let agentText = await askLLM(askDifferentlyPrompt("Sure thing, go ahead and send your content."))
                setMessages((prevMessages) => [
                    ...prevMessages,
                    { type: 'assistant', text: agentText ? agentText : 'Sure thing, go ahead and send your content.' }
                ]);
            }
            if(contentDetails.description && contentDetails.content && contentDetails.style && contentDetails.tone){
                let review = await callAPI(getContentReviewPrompt(contentDetails.description, contentDetails.content, contentDetails.style, contentDetails.tone))
                let finalDraft = await callAPI(finalDraftPrompt(contentDetails.description, contentDetails.content, contentDetails.style, contentDetails.tone, review))
            }
        }

        setLoader(false)
    };

    const produceFiles = async (agentResponse) => {
        setLoader(true)
        let completeFiles = await createNewFiles(instruction, repo.files, repo.newBranch, repo.dir, agentResponse)
        console.log(completeFiles.length)
        if(completeFiles.length > 0){
            setMessages((prevMessages) => [
                ...prevMessages,
                { type: 'assistant', text: "Here is your completed Files.", codeSolution: true, codeList: completeFiles}
            ]);
        }else{
            agentResponse = await askLLM(askDifferentlyPrompt("I apologize, something went wrong. Please try this again."))
            setMessages((prevMessages) => [
                ...prevMessages,
                { type: 'assistant', text: agentResponse ? agentResponse : "I apologize, something went wrong. Please try this again."}
            ]);
        }
        setLoader(false)
    }

    const pushCode = async (codeList) => {
        setLoader(true)
        let changes = await getGitChanges(repo.dir, codeList)
        console.log(changes)
        if(changes){
            setMessages((prevMessages) => [
                ...prevMessages,
                { type: 'assistant', text: "Here is your completed Files.", gitDiff:true, gitDiv: changes}
            ]);
        }else{
            let agentResponse = await askLLM(askDifferentlyPrompt("I apologize, something went wrong. Please try this again."))
            setMessages((prevMessages) => [
                ...prevMessages,
                { type: 'assistant', text: agentResponse ? agentResponse : "I apologize, something went wrong. Please try this again."}
            ]);
        }
        setLoader(false)
    }

    async function callAPI(prompt, code=false) {
        let text = ""
        // Add a new empty assistant message to start updating with streamed chunks
        setMessages((prevMessages) => [
            ...prevMessages,
            { type: 'assistant', text: "", codeCall:code }
        ]);
        let link = "";
        let data;
        let headers = "";
        if(toggleModel === "elf"){
            link = "http://192.168.1.13:8000/Inference/ask_a_pro_stream"
            data = JSON.stringify({ "output_tokens": 12000, "prompt": prompt })
            headers = {
                'Content-Type': "application/json",
                'token': 'fja0w3fj039jwiej092j0j-9ajw-3j-a9j-ea'
            }
        }else{
            link = "http://127.0.0.1:8080/Tasks/stream"
            data = new FormData()
            data.append("prompt", prompt)
            headers = {

            }
        }


        try {
            const response = await fetch(link, {
                method: 'POST',
                headers: headers,
                body: data
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
        console.log(toggleModel)
    }, [toggleModel]);

    useEffect(() => {
        if (messagesEndRef.current) {
            messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [messages]);

    const clearHistory = () => {
        setShowAllTables(false)
        setLoader(false)
        setRunning(false)
        setLastResponse("")
        setInstruction("")
        setRepo({required:"",repoLink:"",branch:"", newBranch:"",allCode:"",dir:"",lastResponse:"",files:""})
        setDataDetails({description:"", rows:"",input:"", label:"", data:[], count:0})
        setContentDetails({description:"",style:"",tone:"", content:""})
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
                    <input type="checkbox" onChange={(e) => setToggleModel(e.target.checked ? "elf" : "oai")}/>
                    <div className="slider slider--0">ELF</div>
                    <div className="slider slider--1">
                        <div></div>
                        <div></div>
                    </div>
                    <div className="slider slider--2"></div>
                    <div className="slider slider--3">CoT</div>
                </label>
            </div>
            <div className="chat-messages">
                {messages.map((msg, index) => (
                    <div
                        key={index}
                        className={`chat-message ${msg.type === 'user' ? 'user-message' : 'assistant-message'}`}
                    >
                        {msg.text}
                        {msg.codeSolution &&
                            msg.codeList.map((file, fileIndex) =>(
                                <div className="fileContainer" key={fileIndex}>
                                    <div className="fileName">{file.FILE_NAME}</div>
                                    <div className="fileCode">{file.FILE_CODE}</div>
                                </div>
                            ))
                        }
                        {msg.codeSolution &&
                            <DiffIcon title="Compare Code and Push" className="icon float-end" onClick={()=>{pushCode(msg.codeList)}}></DiffIcon>
                        }
                        {msg.codeCall &&
                            <CheckIcon title="Produce Files" className="icon float-end" onClick={()=>{produceFiles(msg.text)}}/>
                        }
                        {msg.gitDiff &&
                            <div className="fileContainer">
                                {callParse(msg.gitDiv)}
                            </div>
                        }
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
