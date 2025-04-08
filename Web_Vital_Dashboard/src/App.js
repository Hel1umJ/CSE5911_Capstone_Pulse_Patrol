import React from "react";
import ThemeToggle from "./ThemeToggle";
import GraphWrapper from "./GraphWrapper";
import AccentCard from "./AccentCard";
import FlowRateControlsCard from "./FlowRateControlsCard";

import "./App.css";

import { library } from "@fortawesome/fontawesome-svg-core";
import {
  faHeartPulse,
  faTemperatureHalf,
  faPercent,
} from "@fortawesome/free-solid-svg-icons";


library.add(faHeartPulse, faTemperatureHalf, faPercent);

function App() {
  return (
    <div className="app">
      <div className="row">
        <AccentCard />
      </div>

      <div className="row ecg">
          <h1>Vitals Log</h1>
        <GraphWrapper />
      </div>

      <div className="row controls">
          <FlowRateControlsCard />
      </div>
      
      
      
      
    </div>
  );
}

export default App;