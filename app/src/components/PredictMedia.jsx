import React, { useState, useRef } from "react";
import "../styles/App.css";


function ResultsPage({resultsArray, setShowResults, dialogRef}){
  
  return (
    <>
      <button onClick = {() => {dialogRef.current.close(); setShowResults(false)}}>X</button>
      <div id="resultsContainer">
        {resultsArray.map((result, idx) => (
            <div key={idx} style={{
              backgroundColor: "#e9f4f7",
              borderRadius: "10px",
              padding: "1rem",
              marginBottom: "1.2rem",
              alignItems: "center",
              maxWidth: "200px",
              maxHeight: "250px",
              display:"flex",
              flexDirection:"column",
              overflowX:'hidden',
              overflowY:'auto',
            }}>
              {result.mediaType === "image" ? (
                <img
                  src={result.predictedMedia}
                  alt="Predicted"
                  style={{ width: "80%", maxHeight: "200px", objectFit: "contain", borderRadius: "8px" }}
                />
              ) : (
                <video
                  src={result.predictedMedia}
                  controls
                  style={{ width: "80%", maxHeight: "300px", objectFit: "contain", borderRadius: "8px" }}
                />
              )}
              <ul style={{ marginTop: "1rem", width: "80%", color: "#1e3d48" }}>
                {Object.entries(result.predictions || {}).map(([label, prob]) => (
                  <li key={label}>
                    <strong>{label}:</strong> {prob.toFixed(2)}
                  </li>
                ))}
              </ul>
            </div>
          ))}
      </div>
    </>
  );
}


function TextPrompts({promptsArray, setPromptsArray, promptsRef}) {
    
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
        <div id = "mediaViewContainer" style = {{minHeight:'200px'}}>
            <label>Enter Text Prompts: </label>
            {promptsArray.map((prompt, index) =>(
            <div key={index}>
                <input
                type="text"
                placeholder={"Prompt.."}
                value={prompt}
                onChange={(e) => handlePromptChange(index, e.target.value)}
                name="text_prompts"
                style = {{ width: '66%', padding: '0.5rem', marginBottom: '1.1rem',
                          border: '1px solid #aacbd4', borderRadius: '6px', background: '#f8fcfd',
                          fontSize: '1rem', color: '#1e3d48', transition:'border-color 0.2s ease'}}
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

export default function PredictMedia() {
  
  const [showResults, setShowResults] = useState(false);

  const [filesArray, setFilesArray] = useState([]);
  const [resultsArray, setResultsArray] = useState([]);

  const [promptsArray, setPromptsArray] = useState([""]);
  const promptsRef = useRef(null);
  const dialogRef = useRef(null);

  const handleFileChange = (event) => {
    event.preventDefault();
    const files = event.target.files;
    const newFilesArray = [...files];

    setFilesArray(newFilesArray);
    setResultsArray([]);
  };
  
  const handleUpload = async (event) => {

    event.preventDefault();
    setResultsArray([]);
    for (const file of filesArray) {
      const formData = new FormData();
      let endPoint;
      const cleanedPrompts = Array.isArray(promptsRef.current)
      ? promptsRef.current.map(p => p.trim()).filter(p => p !== "")
      : [];

      if (file.type.startsWith("image/")) {
        formData.append("image", file);
        endPoint = "http://localhost:5000/predict_image";

      } else if (file.type.startsWith("video/")) {
        formData.append("video", file);
        endPoint = "http://localhost:5000/predict_video";
      } else {
        console.warn("Unsupported file type:", file.type);
        continue;
      }
      
      formData.append('prompts', JSON.stringify(cleanedPrompts));
      try {
        const response = await fetch(endPoint, {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const errorText = await response.text();
          throw new Error(errorText || "Upload Failed");
        }

        const data = await response.json();
        
        setResultsArray(prev => [
          ...prev,
          {
            originalFile: file,
            predictedMedia:
              data.mediaType === "image"
                ? "data:image/jpeg;base64," + data.image
                : "data:video/mp4;base64," + data.video,
            mediaType: data.mediaType,
            ...(data.prediction && { predictions: data.prediction }) 
          }
        ]);

      } catch (err) {
        console.error("Upload failed:", err);
      }
    }

  };

  return (
      <>
      <div style = {{display:'flex', justifyContent: 'center', alignItems: 'flex-start'}}>
        < TextPrompts promptsArray = {promptsArray} setPromptsArray = {setPromptsArray} promptsRef = {promptsRef}/>
        <div id = "mediaViewContainer" style = {{minHeight: '200px'}}>
          <form onSubmit={handleUpload}>
            <label>Upload media: </label>
            <input
              type="file"
              accept="image/*,video/*"
              onChange={handleFileChange}
              multiple
            />
            <br /><br />
            <div className = "mediaView">
              {filesArray.map((file, index)=> (
                <div key ={index} style = {{ width:'120px', height: '90px', overflow:'hidden', padding:'0.2rem',}}>
                  {file.type.startsWith("image/") && (
                    <img src={URL.createObjectURL(file)} alt="uploaded" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  )}
                  {file.type.startsWith("video/") && (
                    <video src={URL.createObjectURL(file)} style={{ width: '100%', height: '100%', objectFit: 'cover' }} controls />
                  )}
                </div>
              ))}
            </div>
            <br />
            <button type="submit">
              Upload 
            </button>
            
            {(resultsArray.length > 0)  && (<button type="button" style = {{marginLeft:'240px'}} onClick={() => {dialogRef.current.showModal(); setShowResults(true);}}>
            View Results</button>)}
            <br /><br />
          </form>
        </div>
      </div>
      <dialog ref = {dialogRef} closedby = 'any'>
        {showResults && (<ResultsPage resultsArray = {resultsArray} setShowResults = {setShowResults} dialogRef={dialogRef}/>)}
      </dialog>
    </>
  );

}