import React from 'react';

export default function OptionFilter({ selectedOption, setSelectedOption }) {
  const handleSelectChange = (event) => {
    setSelectedOption(event.target.value);
  };

  return (
    <div className="option-switch-bar">
      <button
        value="image"
        onClick={handleSelectChange}
        className={selectedOption === "image" ? "selected" : ""}
      >
        Predict Media
      </button>
      <button
        value="model"
        onClick={handleSelectChange}
        className={selectedOption === "model" ? "selected" : ""}
      >
        Add Model
      </button>
      <button
        value="webcam"
        onClick={handleSelectChange}
        className={selectedOption === "webcam" ? "selected" : ""}
        >
        Live Camera
      </button>
    </div>
  );
}