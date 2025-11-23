import React, { useState } from "react";
import Header from "./components/Header";
import OptionFilter from "./components/OptionFilter";
import PredictMedia from "./components/PredictMedia";
import AddModel from "./components/AddModel";
import WebcamCanvas from "./components/WebcamCanvasNEW";

export default function App() {

  const [selectedOption, setSelectedOption] = useState("image");

  let modelForm;

  if (selectedOption === "model") {
    modelForm = <AddModel />;
  } else if (selectedOption === "image") {
    modelForm = <PredictMedia />;
  } else if (selectedOption === "webcam") {
    modelForm = <WebcamCanvas />;
  }

  return (
    <div>
      {selectedOption !== "webcam" && <Header />}
      <OptionFilter
        selectedOption={selectedOption}
        setSelectedOption={setSelectedOption}
      />
      {modelForm}
    </div>
  );
}