import React, { useRef, useEffect, useState } from "react";
import io from "socket.io-client";

const socket = io("http://127.0.0.1:5000");

function TextPrompts({ promptsArray, setPromptsArray, promptsRef }) {
    const handlePromptChange = (i, prompt) => {
        const newPromptsArray = [...promptsArray];
        newPromptsArray[i] = prompt;
        setPromptsArray(newPromptsArray);
    };

    const addPromptField = () => {
        setPromptsArray([...promptsArray, ""]);
    };

    const removePromptField = () => {
        setPromptsArray(promptsArray.slice(0, -1));
    };

    return (
        <div id="webcamContainer">
            <label>Enter Text Prompts: </label>
            {promptsArray.map((prompt, index) => (
                <div key={index}>
                    <input
                        id="textPrompts2"
                        type="text"
                        placeholder="Prompt.."
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
                        <button type="button" onClick={removePromptField}>-</button>
                    )}
                </div>
            ))}
            <br />
            <button onClick={() => { promptsRef.current = [...promptsArray] }}>Submit</button>
        </div>
    );
}

export default function WebcamCanvas() {
    
    const [promptsArray, setPromptsArray] = useState([""]);
    const promptsRef = useRef([]);

    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const containerRef = useRef(null);
    const streamRef = useRef(null);
    const intervalRef = useRef(null);

    const [buttonText, setButtonText] = useState("Stop Camera");

    const handleButtonClick = () => {
        if (buttonText === "Stop Camera") {
            setButtonText("Start Camera");
        } else {
            setButtonText("Stop Camera");
        }
    };

    useEffect(() => {
        if (buttonText === "Stop Camera") {
            startCamera();
        } else {
            stopCamera();
        }
    }, [buttonText]);

    const startCamera = () => {
        const constraints = { video: true };
        canvasRef.current.style.display = "";
        navigator.mediaDevices.getUserMedia(constraints)
            .then((stream) => {
                streamRef.current = stream;

                if (videoRef.current) {
                    videoRef.current.srcObject = stream;
                    videoRef.current.onloadedmetadata = () => {
                        const video = videoRef.current;
                        const canvas = canvasRef.current;
                        canvas.width = video.videoWidth;
                        canvas.height = video.videoHeight;
                    };
                    containerRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
                }

                intervalRef.current = setInterval(() => {
                    const video = videoRef.current;
                    const canvas = canvasRef.current;

                    if (!canvas || !video || !streamRef.current) return;

                    const tempCanvas = document.createElement("canvas");
                    tempCanvas.width = video.videoWidth;
                    tempCanvas.height = video.videoHeight;
                    const tempCtx = tempCanvas.getContext("2d");
                    tempCtx.drawImage(video, 0, 0, tempCanvas.width, tempCanvas.height);

                    tempCanvas.toBlob((blob) => {
                        if (!blob) return;
                        const reader = new FileReader();
                        reader.onloadend = () => {
                            const base64Image = reader.result;

                            const cleanedPrompts = promptsRef.current
                                .map((p) => p.trim())
                                .filter((p) => p !== "");

                            socket.emit("frame", {
                                image: base64Image,
                                prompts: cleanedPrompts,
                            });
                        };
                        reader.readAsDataURL(blob);
                    }, "image/jpeg");
                }, 600);
            })
            .catch((err) => {
                console.error("Camera error:", err);
            });
    };

    const stopCamera = () => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach((track) => track.stop());
            streamRef.current = null;
        }

        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }

        if (videoRef.current) {
            videoRef.current.srcObject = null;
        }

        if (canvasRef.current) {
            const ctx = canvasRef.current.getContext("2d");
            ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
            canvasRef.current.style.display = "none";
        }
    };

    useEffect(() => {
        socket.on("prediction", (data) => {
            console.log(data);
            const canvas = canvasRef.current;
            const ctx = canvas.getContext("2d");
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            if (data.type === "yolo") {
                data.data.forEach((item) => {
                    const [x1, y1, x2, y2] = item.box;
                    const label = item.text;
                    ctx.strokeStyle = "red";
                    ctx.lineWidth = 2;
                    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);

                    ctx.font = "16px Arial";
                    ctx.fillStyle = "red";
                    ctx.fillText(label, x1, y1 - 5);
                });
                
            } else if (data.type === "clip") {
                const predictions = data.data;

                ctx.font = "18px Arial";
                ctx.fillStyle = "black";

                let y = 30;
                Object.entries(predictions).forEach(([label, score]) => {
                    ctx.fillText(`${label} (${score.toFixed(2)})`, 10, y);
                    y += 25;
                });
            }
        });

        return () => socket.off("prediction");
    },[]);
    
    return (
        <div className="webcam-container" ref={containerRef} style={{ display: "flex", width: "90vw", margin: "2rem" }}>
            <div className="prompt-tab">
                <button onClick={handleButtonClick} style={{ maxWidth: '300px', margin: '20px auto' }}>{buttonText}</button>
                <TextPrompts promptsArray={promptsArray} setPromptsArray={setPromptsArray} promptsRef={promptsRef} />
            </div>
            <div className="webcam-wrapper">
                <video ref={videoRef} className="webcam-video" autoPlay playsInline muted />
                <canvas ref={canvasRef} className="webcam-canvas" />
            </div>
        </div>
    );
}