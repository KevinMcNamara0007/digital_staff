import {Route, Routes} from 'react-router-dom'
import Developer from "./Developer";
import ContentFormatter from "./ContentFormatter";
import Home from "./Home";

const CompRouter = () => {
    return (
        <Routes>
            <Route path="/" element={<Home/>}/>
            <Route path="/developer" element={<Developer/>}/>
            <Route path="/Content" element={<ContentFormatter/>}/>
        </Routes>
    )
}

export default CompRouter