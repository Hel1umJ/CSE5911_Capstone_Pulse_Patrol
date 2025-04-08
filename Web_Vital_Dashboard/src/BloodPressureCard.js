import React, { useState, useEffect } from "react";
import axios from "axios";
import TextRow from "./TextRow";

function BloodPressureCard() {
  const [data, setData] = useState({ SYS: "...", DIA: "..." });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await axios.get("http://localhost:5000/data");
        
        if (response.data) {
          setData({
            SYS: response.data.bp_sys,
            DIA: response.data.bp_dia
          });
        }
      } catch (error) {
        console.error("Error fetching blood pressure data:", error);
      }
    };

    // Set up polling interval (every 1 second)
    const interval = setInterval(fetchData, 1000);
    
    // Initial fetch
    fetchData();
    
    // Clean up interval on component unmount
    return () => clearInterval(interval);
  }, []);

  function displayValue(key) {
    if (data[key] !== "...") {
      return Math.round(data[key]).toString();
    }
    return "...";
  }

  return (
    <div className="col blood-pres">
      <h3>Blood Pressure</h3>
      <div className="val-col">
        <TextRow
          title={displayValue("SYS")}
          subtitle={"SYS"}
          rev={true}
          large={true}
        />
        <TextRow
          title={displayValue("DIA")}
          subtitle={"DIA"}
          rev={true}
          large={true}
        />
      </div>
    </div>
  );
}

export default BloodPressureCard;