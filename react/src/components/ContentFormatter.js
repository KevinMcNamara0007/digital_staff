import {useEffect, useState} from "react";
import {Button, Col, Form, Nav, Row, Tooltip} from "react-bootstrap";
import Editor from "./Editor";
import DOMPurify from "dompurify";
import parse, {attributesToProps} from "html-react-parser";
import {contentReviewAPI, finalDraftAPI} from "../api/Axios";
import {ReactComponent as TrashIcon} from "../images/trashIcon.svg";

const ContentFormatter = () => {
    const [text, setText] = useState("")
    const [style, setStyle] = useState("AP")
    const [response, setResponse] = useState("")
    const [review, setReview] = useState(null)
    const [running, setRunning] = useState(false)
    const [target, setTarget] = useState("Employees")
    const [progress, setProgress] = useState(null)
    const [view, setView] = useState("")
    const [showTabs, setShowTabs] = useState(false)
    const [sessions, setSessions] = useState([])
    const [sessionIndex, setSessionIndex] = useState(null)
    const [collapsed, setCollapsed] = useState(false)
    const [editMode, setEditMode] = useState(false)
    const [editedDraft, setEditedDraft] = useState("")
    const [expandMode, setExpandMode] = useState(false)

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
    const handleTab = (tab) => {

    }


    const mapper = {
        review: "review",
        finalDraft: "finalDraft"
    }
    const sessionKey = "contentFormatHistory";
    let hist = localStorage.getItem(sessionKey) ? JSON.parse(localStorage.getItem(sessionKey)) : [];
    const getAllSessions = () => {
        let sessionList = []
        if(hist?.length >= 1){
            hist.forEach((item, index)=>{
                sessionList.push(item)
            })
            setSessions(sessionList)
        }
    }
    const handleSubmit = async (e, text) => {
        e.preventDefault()
        if(running === true){
            return;
        }

        setShowTabs(true)
        setRunning(true)
        setProgress({
            [mapper.review]:null,
            [mapper.finalDraft]:null
        })
        setSessionIndex(null)

        let review = "";

        review = await generateReview(text);
        if (!review){
            setRunning(false)
            return;
        }
        setView(mapper.review);

        let finalDraft = await generateFinalDraft(review)
        setView(mapper.finalDraft)

        let sessionObj = {
            "id": hist.length,
            "style": style,
            "text": text,
            [mapper.review]: review,
            [mapper.finalDraft]:finalDraft
        }
        hist.push(sessionObj)
        localStorage.setItem(sessionKey, JSON.stringify(hist))
        setSessions(hist)
        setSessionIndex(sessionObj.id)

        setRunning(false)
    }

    const resetEditMode = () => {
        setEditMode(false)
        setExpandMode(false)
    }

    const clearHistory = () => {
        setSessions([])
        hist = []
        localStorage.removeItem(sessionKey)
    }

    const selectSession = (index) => {
        if(running === false){
            setShowTabs(true)
            setSessionIndex(index)
            setView(mapper.finalDraft)
            setText(hist[index].text)
            setStyle(hist[index].style)
            setReview(hist[index][mapper.review])
            setResponse(hist[index][mapper.finalDraft])
        }
    }

    const handleNew = () => {
        setView("")
        setShowTabs(false)
        setReview("")
        setResponse("")
        setSessionIndex(null)
        resetEditMode()
    }

    const generateReview = async (content) => {
        setProgress(prevState => ({...prevState, [mapper.review]: "running"}))
        return await contentReviewAPI(content, style, localStorage.getItem("model"), "")
            .then((resp)=>{
                setReview(resp.data)
                setProgress(prevState => ({...prevState, [mapper.review]: "complete"}))
                return resp.data
            }).catch((err)=>{
                setProgress(prevState => ({...prevState, [mapper.review]: "fail"}))
                return null
            })
        //LLM Output
    }

    const generateFinalDraft = async (review) => {
        setProgress(prevState => ({...prevState, [mapper.finalDraft]: "running"}))
        return await finalDraftAPI(text, style, review, localStorage.getItem("model"), "")
            .then((resp)=>{
                setResponse(resp.data)
                setProgress(prevState => ({...prevState, [mapper.finalDraft]: "complete"}))
                return resp.data
            }).catch((err)=>{
                setProgress(prevState => ({...prevState, [mapper.finalDraft]: "fail"}))
                return null
            })
    }

    const exportToDoc = (data, type) => {
        let bodyContent = "";
        let filename = "";
        if(type === mapper.review){
            bodyContent = data.replaceAll("\n","<br/>")
            filename = "review.doc"
        }else{
            bodyContent = data;
            filename = "finaldraft.doc"
        }
        let preHtml =
            "<html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'><head><meta charset='utf-8'><title>Export HTML To Doc</title></head><body>";
        let postHtml = "</body></html>";
        let html = preHtml + bodyContent + postHtml

        let docMimeType = 'application/vnd.ms-word';
        let hrefUrl = 'data:'+docMimeType+';charset=utf-8,' + encodeURIComponent(html)

        if(window.navigator.msSaveOrOpenBlob){
            var blob = new Blob(["\ufeff", html], {
                type: "application/msword",
            });
            window.navigator.msSaveOrOpenBlob(blob, filename)
        }else{
            let downloadLinkEle = document.createElement('a')
            let downloadHelperDiv = document.getElementById('downloadHelper')
            downloadHelperDiv.appendChild(downloadLinkEle)
            downloadLinkEle.href = hrefUrl
            downloadLinkEle.download = filename
            downloadLinkEle.click()
            downloadHelperDiv.removeChild(downloadLinkEle)
        }
    }

    const getBarClass = (item) => {
        if(progress === null){
            return ""
        }
        if(progress && progress[mapper[item]] === "running"){
            return "progress-bar"
        }
        if(progress && progress[mapper[item]] === "complete"){
            return "progress-bar-complete"
        }
        if(progress && progress[mapper[item]] === "fail"){
            return "fail"
        }
        return ""
    }

    useEffect(() => {
        getAllSessions()
    }, []);

    return (
        <div className="d-flex w-100">
            <div className="d-flex w-75 px-5 pt-5">
                {view === "" ?
                    <Form>
                        <Row>
                            <div className="contentTabs">
                                <div className="agentTab">
                                    {progress && progress[mapper["review"]] !== null &&
                                        <div disabled={running} onClick={() => {
                                            setView("review")
                                        }} id="planTab" className={`title ${getBarClass("review")}`}>Review
                                        </div>}
                                </div>
                                <div className="agentTab">
                                    {progress && progress[mapper["finalDraft"]] !== null &&
                                        <div disabled={running} onClick={() => {
                                            setView("finalDraft")
                                        }} id="planTab" className={`title ${getBarClass("finalDraft")}`}>Final
                                        </div>}
                                </div>
                            </div>
                            <Form.Group as={Col} sm="3" controlId="style">
                                <Form.Select aria-label="Default select example" disabled={running} value={style}
                                             onChange={(e) => setStyle(e.target.value)} required>
                                    <option value="">Select Style</option>
                                    <option value="Associated Press">AP</option>
                                    <option value="New York Times">NYT</option>
                                    <option value="CNN">CNN</option>
                                </Form.Select>
                            </Form.Group>
                            <Col>
                                <Button className="float-end" disabled={running} type="button" variant={"primary"}
                                        onClick={(e) => handleSubmit(e, text)}>Submit</Button>
                            </Col>
                        </Row>
                        <Form.Group as={Col} className="w-100">
                            <Editor data={text} setData={setText}/>
                        </Form.Group>
                    </Form>
                    : <div className="">
                        <Row className="mt-1">
                            <div className="contentTabs">
                                <div className="agentTab">
                                    {progress && progress[mapper["review"]] !== null &&
                                        <div disabled={running} onClick={() => {
                                            setView("review")
                                        }} id="planTab" className={`title ${getBarClass("review")}`}>Review
                                        </div>}
                                </div>
                                <div className="agentTab">
                                    {progress && progress[mapper["finalDraft"]] !== null &&
                                        <div disabled={running} onClick={() => {
                                            setView("finalDraft")
                                        }} id="planTab" className={`title ${getBarClass("finalDraft")}`}>Final
                                        </div>}
                                </div>
                            </div>
                            <Col className="d-flex justify-content-start pt-3 pb-3">
                                <Button type="button" className={"button-main"} variant={"primary"} disabled={running}
                                        onClick={(e) => handleNew(e)}>New</Button>
                                <Button type="button" variant="link" disabled={running}>
                                    HTML
                                </Button>
                                <Button onClick={()=>{exportToDoc(view === mapper.finalDraft ? response : review, view)}} className="float-end" type="button" variant="link" disabled={running}>
                                    Word
                                    {/*<WordIcon className="icon"></WordIcon>*/}
                                </Button>
                                <div id={"downloadHelper"}/>
                            </Col>
                        </Row>
                        {
                            view === mapper.review ?
                                <div className="">
                                    <div className="review-content">{review}</div>
                                </div>
                                :
                                <>
                                    <div>
                                        {expandMode === false &&
                                            <div className="w-50 m-1">
                                                {/*<Editor data={review} setData={setReview}/>*/}
                                            </div>}
                                        <>
                                            {editMode === true ?
                                                <div className="w-50">
                                                    <div className="container flex-container">
                                                        <Button disabled={running} type="button"
                                                                variant="primary">Done</Button>
                                                    </div>
                                                    <Editor data={response} setData={setResponse}/>
                                                </div> :
                                                <div className="w-100">
                                                    <div className="response ck-content">
                                                        <div className="review-content"><Button className="mb-3 float-end">Edit</Button>{response}</div>
                                                    </div>
                                                </div>
                                            }
                                        </>
                                    </div>
                                </>
                        }
                    </div>
                }
            </div>
            <div className="contentmenu w-25">
                <div className="titleSessions">
                    Sessions
                </div>
                <div className="panel">
                    <span className="clear" onClick={() => {
                        clearHistory()
                    }}><TrashIcon className="img" title="Clear History"/></span>
                    <div className="panelContainer">
                        {sessions.map((item, index) => {
                            return (
                                <button disabled={running === true} key={index}
                                        className={`session w-100 ${index === sessionIndex ? "activeSession" : ""}`}
                                        onClick={() => {
                                            selectSession(index)
                                        }}>{item.text.slice(3, 28)}...</button>
                            )
                        })}
                    </div>
                </div>
            </div>
        </div>
    )
}

export default ContentFormatter