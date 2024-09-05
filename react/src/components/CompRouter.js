import {Route, Routes} from 'react-router-dom'
import Developer from "./Developer";
import DataGenerator from "./DataGenerator";

const CompRouter = () => {
    return (
        <Routes>
            <Route path="/" element={<Developer/>}/>
            <Route path="/data" element={<DataGenerator/>}/>
        </Routes>
    )
}

export default CompRouter