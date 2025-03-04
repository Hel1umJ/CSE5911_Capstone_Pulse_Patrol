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

library.add(faHeartPulse, faTemperatureHalf, faPercent);

function App() {
  return (
    <div className="app">
      <div className="row">
        <AccentCard />
      </div>
      <div className="row ecg">
        <h1>ECG</h1>
        <GraphWrapper />
      </div>
      <div className="row lg-accent-card">
        <div className="accent-col">
          <div class="accent-row">
            <BloodPressureCard />
          </div>
          <div class="accent-row">
            <FlowRateCard />
          </div>
        </div> 
      </div>
    </div>
  );
}

export default App;
