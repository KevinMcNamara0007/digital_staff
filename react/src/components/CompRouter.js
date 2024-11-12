import {Route, Routes} from 'react-router-dom'
import Home from "./Home";

const CompRouter = () => {
    return (
        <Routes>
            <Route path="/" element={<Home/>}/>
        </Routes>
    )
}

export default CompRouter