import React, { useState, useEffect } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import axios from "axios";

import "./SmallSensorCard.css";
import TextRow from "./TextRow";

function SmallSensorCard({ iconName, title, path, unit }) {
  const [data, setData] = useState("...");

  // Fetch data from the backend based on the path prop
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get("/data");
        
        // Map the path to the appropriate field in the response
        // We'll use a mapping object to handle different paths
        const dataMapping = {
          "/heart_rate_val": "heart_rate",
          "/sp02_val": "spo2"
        };
        
        const field = dataMapping[path];
        if (field && response.data && response.data[field] !== undefined) {
          setData(response.data[field]);
        }
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    // Set up polling interval
    const interval = setInterval(fetchData, 1000);
    
    // Initial fetch
    fetchData();
    
    // Clean up interval on component unmount
    return () => clearInterval(interval);
  }, [path]);

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