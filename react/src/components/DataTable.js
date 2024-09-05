import {useEffect, useState} from "react";
import {Button, Table} from "react-bootstrap";

const DataTable = (props) => {
    const {data} = props;
    const showMatrix = props.showMatrix;
    const setShowMatrix = props.setShowMatrix;
    const showBalancer = props.showBalancer;
    const setShowBalancer = props.setShowBalancer;
    const showTable = props.showTable;
    const setShowTable = props.setShowTable;

    useEffect(() => {
        console.log(showTable)
    }, [showTable]);

    const showDataMatrix = () => {
        setShowMatrix(true)
        setShowBalancer(false)
        setShowTable(false)
    }
    const showDataBalancer = () => {
        setShowMatrix(false)
        setShowBalancer(true)
        setShowTable(false)
    }
    const showDataTable = () => {
        setShowMatrix(false)
        setShowBalancer(false)
        setShowTable(true)
    }

    const [cols,setCols] = useState([])
    const [excelContent, setExcelContent] = useState("")

    const exportToExcel = () => {
        let excelContent = "";
        let excelHeader = cols.join(',')+"\n";
        excelContent = excelHeader;
        data.forEach(item => {
            let rowContent = "";
            cols.forEach((key, index)=>{
                if(key !== "row"){
                    rowContent = rowContent + `\"${item[key]}\"`
                    if (index !== cols.length-1){
                        rowContent += ","
                    }
                }
            })
            excelContent = excelContent + rowContent + "\n";
        });
        const csvContent = `data:text/csv;charset=utf-8,${excelContent}`;
        setExcelContent(csvContent)
    }

    const copyToClipboard = async()=>{
        let filteredData = data.map(({row, ...item})=>item);
        let copyContent = JSON.stringify(filteredData)
        await navigator.clipboard.writeText(copyContent)
    }
    useEffect(()=>{
        if(data && data[0]){
            let cols = Object.keys(data[0]).filter(item => item !== "row")
            setCols(cols)
        }
    },[data])

    return(
        <div>
            <div className="mt-5 exportControls">
                {showMatrix !== true &&
                    <Button variant="success" className="ms-1 mt-3" onClick={()=>{showDataMatrix()}}>
                        View Matrix
                    </Button>
                }
                {showBalancer !== true &&
                    <Button variant="success" className="ms-1 mt-3"  onClick={()=>{showDataBalancer()}}>
                        View Balancer
                    </Button>
                }
                {showTable !== true &&
                    <Button variant="success" className="ms-1 mt-3"  onClick={()=>{showDataTable()}}>
                        View Table
                    </Button>
                }
                <button variant="success" className="btn exportBtn ms-1 mt-3" disabled={!data} onClick={()=>{exportToExcel()}} data-tooltip-id="excelTooltip">
                    <a className="center" href={excelContent} download="data.csv">
                        <span>Excel</span>
                    </a>
                </button>
                <div id="downloadHelper"></div>
            </div>
                {
                    showTable &&
                    <div className="dataTable flexChildStretch flexStretchHeightWrapper scrollBar">
                        <Table striped bordered hover variant="dark" className="flexChildStretch flexStretchHeightWrapper1">
                            <thead>
                            <tr></tr>
                            </thead>
                            <tbody className="flexChildStretch scrollbar">
                            <tr key={"rowHEader"} id="rowHeader">
                                <td>#</td>
                                {cols?.map((key,index)=>{
                                    if(key !== "row"){
                                        return (
                                            <td key={"dataTablerHeader"+index}>{key}</td>
                                        )
                                    }
                                })}
                            </tr>
                            {data?.map((row,i)=>{
                                return(
                                    <tr key={"row"+i}>
                                        <td>{i+1}</td>
                                        {cols.map((key,j)=>{
                                            if(key !== "row"){
                                                return(
                                                    <td key={"row"+i+"col"+j}>{row[key]}</td>
                                                )
                                            }

                                        })}
                                    </tr>
                                )
                            })}
                            </tbody>
                        </Table>
                    </div>
                }
        </div>
    )
}

export default DataTable