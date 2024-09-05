import {useEffect, useState} from "react";
import staffLogo from '../images/stafflogo.png'
import {Link} from "react-router-dom";

const SideBar = () => {
    const [model,setModel] = useState("oai")

    useEffect(() => {
        if(localStorage.getItem("model")){
            localStorage.setItem("model","oai")
            setModel("oai")
        }else{
            localStorage.setItem("model","oai")
        }
    }, []);
    const toggleDarkMode = () => {
        document.body.classList.toggle("darkMode");
    }

    const toggleModel = (modelType) => {
        setModel(modelType)
        localStorage.setItem("model",modelType)
    }

    return (
        <div className="sideBar">
            <div className="mainTitle"><h1><img alt="logo" src={staffLogo}/>E-Staff</h1></div>
            <div className="wrapper">
                <div className="toggle" onClick={() => {
                    toggleDarkMode()
                }}>
                    <input className="toggle-input" type="checkbox"/>
                    <div className="toggle-bg"></div>
                    <div className="toggle-switch">
                        <div className="toggle-switch-figure"></div>
                        <div className="toggle-switch-figureAlt"></div>
                    </div>
                </div>
            </div>
            <div className="navContainer">
                <div className="subTitle">
                    Software & Data
                </div>
                <div className="linkContainer">
                    <div className="link"><Link to={"/"}>Developer</Link></div>
                    <div className="link"><Link to={"/data"}>Annotator</Link></div>
                </div>
                <div className="subTitle">
                    Future
                </div>
                <div className="linkContainer">
                    <div className="link disabled">Content Formatter</div>
                    <div className="link disabled">Jira Groomer</div>
                    <div className="link disabled">Marketing</div>
                    <div className="link disabled">Insurance</div>
                </div>
            </div>
            <div className="modelText">
                Choose your AI model of choice.<br/>
                (ELF) Expert Level Framework<br/>
                (OAI) OpenAI GPT-4o
            </div>
            <div className="modelContainer">
                <label className="switch">
                    <input type="checkbox"/>
                    <div className="slider slider--0" onClick={() => {
                        toggleModel("oai")
                    }}>ELF
                    </div>
                    <div className="slider slider--1">
                        <div></div>
                        <div></div>
                    </div>
                    <div className="slider slider--2"></div>
                    <div className="slider slider--3" onClick={() => {
                        toggleModel("elf")
                    }}>OAI
                    </div>
                </label>
            </div>
        </div>
    )
}

export default SideBar