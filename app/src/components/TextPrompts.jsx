import React from 'react';

export default function TextPrompts({promptsArray, setPromptsArray, promptsRef, divID}) {

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

    return (
        <div id= {divID}>
            <label>Enter Text Prompts: </label>
            {promptsArray.map((prompt, index) =>(
            <div key={index}>
                <input
                id = "textPrompts2"
                type="text"
                placeholder={"Prompt.."}
                value={prompt}
                onChange={(e) => handlePromptChange(index, e.target.value)}
                name="text_prompts"
                />
                <div className = "divider" />
                {index === promptsArray.length - 1 && (
                <>
                    <button type="button" onClick={addPromptField}>+</button>
                </>
                )}
                <div className = "divider" />
                {index === promptsArray.length - 1 && index !== 0 && (
                <button type="button" onClick = {removePromptField}>-</button>
                )}
            </div>
            ))}
            <br />
            <button onClick={() => { promptsRef.current = [...promptsArray] }}>Submit</button>
        </div>
    );
}
