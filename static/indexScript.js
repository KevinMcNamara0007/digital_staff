let code = "Here is the cleaned code:\n\ngeneral.py:\n\n```python\ndef add(x, y):\n return x + y\n\ndef subtract(x, y):\n return x - y\n\ndef multiply(x, y):\n return x * y\n\ndef divide(x, y):\n return x / y\n```\n\nutilities/__init__.py:\n\n```python\nimport json\n\nif sys.version_info >= (3, 7):\n def print_colorized_text(text):\n pass\n if not sys.stdout.isattt:\n def colorize(text, color):\n return f\"\\033[{color}m{text}\\033[0m\"\n return colorize(text, \"31\")\n else:\n return text\n else:\n return print_colorized_text\n else:\n pass\n\ndef json_load(json_string):\n return json.loads(json_string)\n```\n\nutilities/git.py:\n\n```python\nimport subprocess\nimport re\n\ndef get_current_branch():\n result = subprocess.run(\"git branch\", shell=True, stdout=subprocess.PIPE).stdout.decode(\"utf-8\").split(\"\\n\")[1:-1] if result else None\n return [i for i in result if not i.startswith(\"*\")][0] if result else None\n\ndef get_git_status():\n result = subprocess.run(\"git status\", shell=True, stdout=subprocess.PIPE).stdout.decode(\"utf-8\")\n return re.search(r\"([\\d\\W]+)\\s+(\\d{2,})[ ]+\\[(.+?)\\]\", result.decode(\"utf-8\")) if result else None\n```\n\nutilities/inference.py:\n\n```python\nimport numpy as np\nimport tensorflow as tf\n\ndef load_model(model_path):\n return tf.keras.models.load_model(model_path)\n\ndef predict(model, input_data):\n if not (isinstance(input_data, np.ndarray) or isinstance(input_data, list)):\n raise TypeError(\"Input data must be a numpy array or a list.\")\n return model.predict(input_data)\n```"
window.onload = function () {
    // document.getElementById("newCode").innerText = code.replaceAll('`')
    document.getElementById("inputs").style.display = "flex"
    document.getElementById("responses").style.display = "none"
    document.getElementById("loader").style.display = "none"
}


function digitalAgentAPI(){
    let formData = new FormData();
    formData.append("user_prompt", document.getElementById("instruction").value);
    formData.append("https_clone_link", document.getElementById("repo").value);
    formData.append("original_code_branch", document.getElementById("branch").value);
    formData.append("new_branch_name", document.getElementById("newBranch").value);
    displayHideInputs();
    displayHideLoader();
    $.ajax({
        type: "POST",
        url: "/Tasks/RunTask",
        data: formData,
        processData: false,
        contentType: false,
        success: function (data) {
            displayHideLoader();
            displayHideResponses();
            let completeString = "Final Code \n" + data["Code Final"] + "\n\n Test Final \n " + data["Test Final"] + "\n\n Dev 1 \n" +
                data["Developer 1"] + "\n\n Dev 2 \n" + data["Developer 2"] + "\n\n Dev 3 \n" + data["Developer 3"] +
                "\n\n Dev 4 \n" + data["Developer 4"] + "\n\n Dev 5 \n" + data["Developer 5"] + "\n\n Dev 6 \n" + data["Developer 6"] +
                "\n\n Dev 7 \n" + data["Developer 7"] + "\n\n Dev 8 \n" + data["Developer 8"] + "\n\n Dev 9 \n" + data["Developer 9"] +
                "\n\n Dev 10 \n" + data["Developer 10"]
            document.getElementById("newCode").innerText = completeString.replaceAll('`')

        },
        error: function (xhr, ajaxOptions, thrownError) {
            displayHideLoader();
            displayHideInputs();
            displayAlert("Agent API has failed")
        },
    });
}
const delay = ms => new Promise(res => setTimeout(res, ms));
const displayAlert = msg => {
    document.getElementById("popup").style.display = "block";
    document.getElementById("alert").innerText = msg;
    delay(3000).then(()=>{
        document.getElementById("alert").innerText = "";
        document.getElementById("popup").style.display = "none";
    })
}

const displayHideInputs = () =>{
    const inputs = document.getElementById("inputs");
    inputs.style.display = inputs.style.display !== "flex" ? "flex" : "none";
}
const displayHideResponses = () => {
    const responses = document.getElementById("responses");
    responses.style.display = responses.style.display !== "flex" ? "flex" : "none";
}

const displayHideLoader = () => {
    const loader = document.getElementById("loader");
    loader.style.display = loader.style.display !== "flex" ? "flex" : "none";
}

const reset = () => {
    displayHideResponses();
    displayHideInputs();
}