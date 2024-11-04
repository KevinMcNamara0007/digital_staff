import {useEffect, useRef, useState} from "react";
import {ReactComponent as ArrowIcon} from "../images/arrowIcon.svg"

const CoTDev = () => {
    const [showPlan, setShowPlan] = useState(false)
    const [running, setRunning] = useState(false)
    const [plan, setPlan] =useState("")
    const [result, setResult] = useState("")
    const [status, setStatus] = useState("")
    const [instruction, setInstruction] = useState("")
    const responseRef = useRef(null);
    const planRef = useRef(null);
    async function handleSubmit(){
        if(running === false){
            setRunning(true);
            await callAPI(instruction)
            setRunning(false);
        }
    }
    let resultChunks = false;


    const togglePlanResult = () => {
        setShowPlan(!showPlan)
    }

    useEffect(() => {
        if (responseRef.current) {
            requestAnimationFrame(() => {
                responseRef.current.scrollTop = responseRef.current.scrollHeight;
            });
        }
    }, [result]);

    useEffect(() => {
        if (planRef.current) {
            requestAnimationFrame(() => {
                planRef.current.scrollTop = planRef.current.scrollHeight;
            });
        }
    }, [plan]);


    async function callAPI(prompt) {
        setStatus("Thinking")
        setResult("")
        setPlan("")
        resultChunks = false
        try {
            const response = await fetch("http://127.0.0.1:8000/Inference/ask_a_pro_stream", {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'token': 'fja0w3fj039jwiej092j0j-9ajw-3j-a9j-ea' // Consider keeping this secure
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
                let text = ""
                // Decode the chunk and append it to the result
                text += decoder.decode(value, { stream: true });
                const responseElement = document.getElementById("response");
                const planElement = document.getElementById("plan")
                if(text.includes("!Final!")){
                    resultChunks = true
                    text = ""
                    setStatus("Answering")
                }
                if(resultChunks === true){
                    setResult(prevState => prevState + text)
                }else{
                    setPlan(prevState => prevState + text)
                }

            }
        } catch (error) {
            console.error('API call failed:', error);
        }
    }

    return (
        <div className="cotContainer">
            <div>
                <div>
                    <div className="">
                        <button className="thinkButton" id="think" onClick={()=>{togglePlanResult()}}>{status}</button>
                    </div>
                </div>
                <div className="responseContainer">
                    <div className="response">
                        {showPlan === true &&
                            <div ref={planRef} id="plan">
                                {plan}
                            </div>
                        }
                        <div ref={responseRef} id="response">
                            {result}
                        </div>
                    </div>
                </div>
                <div className="promptContainer">
                    <label>
                        <input id="instruction" onChange={(e)=>{setInstruction(e.target.value)}} type="text" title="instruction"
                               placeholder="Enter your instructions here"/>
                    </label>
                    <button className="searchImage" onClick={()=>{handleSubmit()}}><ArrowIcon className="img"/>
                    </button>
                </div>
            </div>
        </div>
    )
}

export default CoTDev