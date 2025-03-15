import React, { useEffect, useState } from "react";
import axios from "axios";
import "./FlowRateCard.css";

function FlowRateCard() {
  const [flowRate, setFlowRate] = useState(0);
  
  // Fetch the current flow rate from the backend
  useEffect(() => {
    const fetchFlowRate = async () => {
      try {
        const response = await axios.get("/data");
        if (response.data && response.data.flow_rate !== undefined) {
          // Get the flow rate value as an integer
          const flowRateValue = Math.round(response.data.flow_rate);
          
          // Update state if different from current value
          if (flowRateValue !== flowRate) {
            console.log("Updating flow rate from server:", flowRateValue, "mL/min");
            setFlowRate(flowRateValue);
          }
        }
      } catch (error) {
        console.error("Error fetching flow rate:", error);
      }
    };

    // Poll for updates every two seconds
    const interval = setInterval(fetchFlowRate, 1000);
    
    // Initial fetch
    fetchFlowRate();
    
    // Clean up interval on component unmount
    return () => clearInterval(interval);
  }, [flowRate]);

  // Increase flow rate by 1
  const increaseFlowRate = () => {
    // Ensure we don't exceed maximum flow rate (30)
    const newValue = Math.min(30, flowRate + 1);
    
    if (newValue !== flowRate) {
      // Update local state
      setFlowRate(newValue);
      
      // Send to server
      sendFlowRateToServer(newValue);
    }
  };

  // Decrease flow rate by 1
  const decreaseFlowRate = () => {
    // Ensure we don't go below 0
    const newValue = Math.max(0, flowRate - 1);
    
    if (newValue !== flowRate) {
      // Update local state
      setFlowRate(newValue);
      
      // Send to server
      sendFlowRateToServer(newValue);
    }
  };

  // Helper function to send flow rate to the server
  const sendFlowRateToServer = (value) => {
    console.log("Setting flow rate to:", value, "mL/min");
    
    axios.post(
      "/flow_rate",
      { flow_rate: value },
      { headers: { "Content-Type": "application/json" } }
    ).then(response => {
      console.log("Flow rate updated successfully:", response.data);
    }).catch(error => {
      console.error("Error updating flow rate:", error);
    });
  };

  return (
    <div className="card col">
      <h1>Flow Rate Control</h1>
      <div className="flow-rate-simple">
        <div className="flow-rate-value">
          <span className="value">{flowRate}</span>
          <span className="unit">mL/min</span>
        </div>
        <div className="flow-control-buttons">
          <button className="flow-button" onClick={decreaseFlowRate}>−</button>
          <button className="flow-button" onClick={increaseFlowRate}>+</button>
        </div>
      </div>
    </div>
  );
}

export default FlowRateCard;