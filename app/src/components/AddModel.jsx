import React, { useState } from "react";

export default function AddModel(){

  const [promptsArray, setPromptsArray] = useState([""]);

  const handlePromptChange = (i, prompt) => {
    const newPromptsArray = [...promptsArray];
    newPromptsArray[i] = prompt;

    setPromptsArray(newPromptsArray);
  };

  const addPromptField = () => {
    setPromptsArray([...promptsArray, ""]);
  };

  const removePromptField = () => {
    const newPromptsArray = promptsArray.slice(0, -1);
    setPromptsArray(newPromptsArray)
  };

  function FormSubmitted(event){
    event.preventDefault(); 
    const formData = new FormData();
    const form = event.target;
    const file = form.model_file.files[0];
    const name = form.model_name.value;

    formData.append("model", file);
    formData.append("name", name);
    promptsArray.forEach(prompt => formData.append('prompt', prompt))

    fetch("http://localhost:5000/add_model", {
      method: "POST",
      body: formData,
    })  
      .then((res) => res.json())
      .then((data) => {
        console.log("Server response:", data);
      })
      .catch((err) => {
        console.error("Error adding model:", err);
      });
    };

  return (
    <div className = "container">
      <form onSubmit={FormSubmitted} id = "addModel" name = "addModel">
        <label>Upload Model File: </label>
        <input type="file" id="model_file" name="model_file" accept=".pt" />
        <br/> <br/>
        <label>Enter Model Name: </label>
        <input type="text" id = "model_name" name="model_name" placeholder="model name.."/>
        <br/> <br/>
        <label>Enter Text Prompts: </label>
        {promptsArray.map((prompt, index) =>(
          <div key={index}>
            <input
              id ="textPrompts"
              type="text"
              placeholder={"Prompt.."}
              value={prompt}
              onChange={(e) => handlePromptChange(index, e.target.value)}
              name="text_prompts"
            />
            <div className="divider" />
            {index === promptsArray.length - 1 && (
              <>
                <button type="button" onClick={addPromptField}>+</button>
              </>
            )}
            <div className="divider" />
            {index === promptsArray.length - 1 && index !== 0 && (
              <button type="button" onClick = {removePromptField}>-</button>
            )}
          </div>
        ))}
        <br/>
        <button type="submit">Add Model</button>
      </form>
    </div>
  );
}