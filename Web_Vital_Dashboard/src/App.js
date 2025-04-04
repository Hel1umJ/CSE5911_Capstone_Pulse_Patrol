import React from "react";
import ThemeToggle from "./ThemeToggle";
import GraphWrapper from "./GraphWrapper";
import AccentCard from "./AccentCard";

import "./App.css";

import { library } from "@fortawesome/fontawesome-svg-core";
import {
  faHeartPulse,
  faTemperatureHalf,
  faPercent,
} from "@fortawesome/free-solid-svg-icons";
import FlowRateCard from "./FlowRateCard";
import BloodPressureCard from "./BloodPressureCard";
import ProcedureControlCard from "./ProcedureControlCard";

library.add(faHeartPulse, faTemperatureHalf, faPercent);

function App() {
  return (
    <div className="app">
      <div className="row">
        <AccentCard />
      </div>
      
      <div className="row controls">
        <div className="controls-grid">
          <FlowRateCard />
          <ProcedureControlCard />
        </div>
      </div>
      
      <div className="row ecg">
        <h1>Heart Rate Monitoring</h1>
        <GraphWrapper />
      </div>
      
      <div className="row lg-accent-card">
        <div className="accent-col">
          <div className="accent-row">
            <BloodPressureCard />
          </div>
        </div> 
      </div>
    </div>
  );
}

export default App;