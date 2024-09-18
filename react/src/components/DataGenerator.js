import {Button, Col, Form, Row} from "react-bootstrap";
import {useEffect, useState} from "react";
import {generateDataAPI} from "../api/Axios";
import DataTable from "./DataTable";

const DataGenerator = () => {
    let baselink = "http://127.0.0.1:8080"
    //form vars
    const [dataDescription, setDataDescription] = useState("");
    const [rows,setRows] = useState("")
    const [input, setInput] = useState({"field":"input", "description":""})
    const [label, setLabel] = useState({"field":"label", "description":""})
    const [fields, setFields] = useState([input,label])
    const [data,setData] = useState("")
    const [status, setStatus] = useState("null")

    const [display, setDisplay] = useState("init");

    const [running, setRunning] = useState(false)

    const [showMatrix, setShowMatrix] = useState(false)
    const [showBalancer, setShowBalancer] = useState(false)
    const [showTable, setShowTable] = useState(false)

    useEffect(() => {
        console.log(showTable)
    }, [showTable]);

    const handleSubmit = async()=>{
        if(running === false){
            setRunning(true)
            setShowTable(false)
            setShowMatrix(false)
            setShowBalancer(false)
            setStatus("running")

            let data = await generateData();
            let sessionObj = {
                id: "",
                "generate": {
                    "data": dataDescription,
                    "dataSize": rows,
                    "dataFields": fields
                },
                "result": data
            }
            setRunning(false)
            setShowTable(true)
        }
    }

    const generateData = async() => {
        return await generateDataAPI(dataDescription, rows, [input,label], localStorage.getItem("model"))
            .then((response)=>{
                if(!response){
                    throw new Error("Error")
                }
                let resp = response.data
                setData(resp)
                setDisplay("result")
                setStatus("complete")
                return resp
            }).catch((err)=>{
                setStatus("fail")
                return []
            })
    }

    const getBarClass = () => {
        if(status === "null"){
            return ""
        }
        if(status === "running"){
            return "progress-bar"
        }
        if(status === "complete"){
            return "progress-bar-complete"
        }
        if(status === "fail"){
            return "fail"
        }
        return ""
    }


    return (
        <div className="mainContainer w-100 h-100">
            <div className="container-fluid w-75 px-5 pt-5">
                <div className="dataTabs">
                    <div className="agentTab">
                        {status !== "null" &&
                            <div disabled={running} id="planTab" className={`title ${getBarClass()}`}>Annotating
                            </div>}
                    </div>
                </div>
                {display !== "result" &&
                    <Form>
                        <h3 className="text-center">Data Annotation Contract</h3>
                        <div className="mt-2 mb-2">
                            <b>Annotation Details</b>
                        </div>
                        <Form.Group as={Row} className="mb-3">
                            <Form.Label column sm="2">
                                Name
                            </Form.Label>
                            <Col sm="10">
                                <Form.Control value={dataDescription}
                                              placeholder="What will this data set be about? EX: 10-20 worded sentences"
                                              onChange={(e) => {
                                                  setDataDescription(e.target.value)
                                              }}></Form.Control>
                            </Col>
                        </Form.Group>
                        <Form.Group as={Row} className="mb-3">
                            <Form.Label column sm="2">
                                Number of Rows
                            </Form.Label>
                            <Col sm="10">
                                <Form.Control type="number" value={rows} placeholder="Enter a number from 0-100"
                                              onChange={(e) => {
                                                  setRows(e.target.value)
                                              }}></Form.Control>
                            </Col>
                        </Form.Group>
                        <div className="mt-2 mb-2">
                            <b>Input and Label</b>
                        </div>
                        <Form.Group as={Row} className="mb-3" controlId={"formControl"} key={"dataField"}>
                            <Col sm="2">
                                <Form.Control placeholder="Input. EX: sentence" required value={input.field}
                                              onChange={(e) => {
                                                  setInput(prev => ({...prev, field: e.target.value}))
                                              }}/>
                            </Col>
                            <Col sm="10">
                                <Row>
                                    <Col>
                                        <Form.Control required value={input.description} onChange={(e) => {
                                            setInput(prev => ({...prev, description: e.target.value}))
                                        }}
                                                      placeholder="Label Description Ex: 10-20 word sentence"/>
                                    </Col>
                                </Row>
                            </Col>
                        </Form.Group>
                        <Form.Group as={Row} className="mb-3" controlId={"formControl"} key={"dataLabel"}>
                            <Col sm="2">
                                <Form.Control placeholder="Label. EX: Genre" required value={label.field}
                                              onChange={(e) => {
                                                  setLabel(prev => ({...prev, field: e.target.value}))
                                              }}/>
                            </Col>
                            <Col sm="10">
                                <Row>
                                    <Col>
                                        <Form.Control required value={label.description} onChange={(e) => {
                                            setLabel(prev => ({...prev, description: e.target.value}))
                                        }}
                                                      placeholder="Label Description Ex: Only Fiction or Non Fiction as Genre"/>
                                    </Col>
                                </Row>
                            </Col>
                        </Form.Group>
                        <Button disabled={running} className="float-end" type="button" variant="primary" onClick={() => {
                            handleSubmit()
                        }}>Submit</Button>
                    </Form>
                }
                {display === "result" &&
                    <div>
                        <Button variant="primary" className="float-end mt-3 mb-3" onClick={() => {
                            setDisplay("init")
                        }}>New Contract</Button>
                        <DataTable data={data} showMatrix={showMatrix} setShowMatrix={setShowMatrix}
                                   showTable={showTable} setShowTable={setShowTable} showBalancer={showBalancer}
                                   setShowBalancer={setShowBalancer}/>
                        {showMatrix && <div>
                            <img className="img-fluid mb3 p-1" alt="matrix"
                                 src={`${baselink}/Data/data_matrix?key=${label.field}&source=${input.field}&training_set=${JSON.stringify(data)}`}
                            />
                        </div>}
                        {showBalancer && <div>
                            <img className="img-fluid mb3 p-1" alt="matrix"
                                 src={`${baselink}/Data/data_balancer?key=${label.field}&source=${input.field}&training_set=${JSON.stringify(data)}`}
                            />
                        </div>}
                    </div>
                }
            </div>
        </div>
    )
}

export default DataGenerator