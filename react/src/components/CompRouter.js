import {Route, Routes} from 'react-router-dom'
import Developer from "./Developer";
import DataGenerator from "./DataGenerator";
import ContentFormatter from "./ContentFormatter";

const CompRouter = () => {
    return (
        <Routes>
            <Route path="/" element={<Developer/>}/>
            <Route path="/data" element={<DataGenerator/>}/>
            <Route path="/Content" element={<ContentFormatter/>}/>
        </Routes>
    )
}

export default CompRouter