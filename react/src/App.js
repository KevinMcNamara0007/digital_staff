import {useEffect, useState} from "react";
import Developer from "./components/Developer";
import SideBar from "./components/SideBar";
import CompRouter from "./components/CompRouter";

function App() {

  return (
    <div className="windowContainer">
        <SideBar/>
        <CompRouter/>
    </div>
  );
}

export default App;
