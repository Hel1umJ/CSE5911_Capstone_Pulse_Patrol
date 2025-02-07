import React, { useState, useEffect } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import axios from "axios";

import "./SmallSensorCard.css";
import TextRow from "./TextRow";

function SmallSensorCard({ iconName, title, path, unit }) {
  const [data, setData] = useState("...");

  // useEffect(() => {
  //   if (path !== null) {
  //     const interval = setInterval(async () => {
  //       const result = await axios(path);
  //       const value = result.data["value"];
  //       //console.log(title + ": " + value + unit);
  //       setData(value);
  //     }, 1000);

  //     return () => clearInterval(interval);
  //   }
  // }, [path, title, unit]);

  function displayValue() {
    // Hard coding values for now
    if (title === "Body Temp") {
      return "98.6";
    } else if (title === "CO₂") {
      return "2";
    }
    // end hard coded values

    if (data !== "...") {
      return Math.round(data).toString();
    }
    return "...";
  }

  return (
    <div className="small-sensor-card">
      <div className="circle-icon">
        <FontAwesomeIcon icon={iconName} className="icon" />
      </div>
      <h3>{title}</h3>
      <TextRow title={displayValue()} subtitle={unit} />
    </div>
  );
}

export default SmallSensorCard;
