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
      <ThemeToggle />
      <div className="row">
        <div className="grid">
          <div className="card">
            <h1>ECG</h1>
            <GraphWrapper />
          </div>
          <div className="row">
            <BloodPressureCard />
            <FlowRateCard />
          </div>
        </div>
        <AccentCard />
      </div>
    </div>
  );
}

export default App;
