import {Route, Routes} from 'react-router-dom'
import Developer from "./Developer";
import DataGenerator from "./DataGenerator";
import ContentFormatter from "./ContentFormatter";
import CoTDev from "./CoTDev";

const CompRouter = () => {
    return (
        <Routes>
            <Route path="/" element={<Developer/>}/>
            <Route path="/data" element={<DataGenerator/>}/>
            <Route path="/Content" element={<ContentFormatter/>}/>
            <Route path="/CoT" element={<CoTDev/>}/>
        </Routes>
    )
}

export default CompRouter