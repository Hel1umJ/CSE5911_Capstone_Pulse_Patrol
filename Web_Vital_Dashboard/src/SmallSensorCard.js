import React, { useState, useEffect } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import axios from "axios";

import "./SmallSensorCard.css";
import TextRow from "./TextRow";

function SmallSensorCard({ iconName, title, path, unit }) {
  const [data, setData] = useState("...");

  function displayValue() {
    if (data !== "...") {
      return Math.round(data).toString();
    }
    return "...";
  }

  return (
    <div className="small-sensor-card">
      <div className="sensor-title">
        <div className="circle-icon">
          <FontAwesomeIcon icon={iconName} className="icon" />
        </div>
        <h3>{title}</h3>
      </div>
      <div className="sensor-value">
        <TextRow title={displayValue()} subtitle={unit} />
      </div>
    </div>
  );
}

export default SmallSensorCard;
