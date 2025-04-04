import React, { useState, useEffect, useRef } from "react";
import { io } from "socket.io-client";
import "./FlowRateCard.css";

function FlowRateCard() {
  const [flowRate, setFlowRate] = useState(0);
  const [socketConnected, setSocketConnected] = useState(false);
  const [procedureRunning, setProcedureRunning] = useState(false);
  const socketRef = useRef(null);
  const localChangeRef = useRef(false);
  
  useEffect(() => {
    // Get the server URL
    const serverUrl = "http://localhost:5000";

    console.log("Connecting to Socket.IO server at:", serverUrl);
    
    // Initialize Socket.IO connection
    const socket = io(serverUrl, {
      transports: ["websocket", "polling"],
      withCredentials: false
    });
    
    // Store the socket in the ref
    socketRef.current = socket;
    
    // Setup event listeners
    socket.on("connect", () => {
      console.log("Connected to WebSocket server");
      setSocketConnected(true);
    });
    
    socket.on("connect_error", (error) => {
      console.error("Socket connection error:", error);
      setSocketConnected(false);
    });
    
    socket.on("disconnect", () => {
      console.log("Disconnected from WebSocket server");
      setSocketConnected(false);
    });
    
    socket.on("flow_rate_update", (data) => {
      console.log("Received flow rate update:", data);
      
      // Only update if it wasn't a local change
      if (!localChangeRef.current) {
        setFlowRate(data.flow_rate);
      } else {
        // Reset the flag
        localChangeRef.current = false;
      }
    });
    
    // Handler for procedure state updates
    socket.on("procedure_state_update", (data) => {
      console.log("Received procedure state update:", data);
      setProcedureRunning(data.running);
    });
    
    // Initial data fetch to get current flow rate
    const fetchInitialData = async () => {
      try {
        const response = await fetch("/data");
        const data = await response.json();
        
        if (data) {
          setFlowRate(data.flow_rate || 0);
          setProcedureRunning(data.procedure_running || false);
        }
      } catch (error) {
        console.error("Error fetching initial data:", error);
      }
    };
    
    fetchInitialData();
    
    // Cleanup on unmount
    return () => {
      socket.disconnect();
    };
  }, []);
  
  // Increase flow rate by 1
  const increaseFlowRate = () => {
    if (!socketConnected) {
      console.error("Socket not connected - cannot update flow rate");
      return;
    }
    
    // Ensure we don't exceed maximum flow rate (30)
    const newValue = Math.min(30, flowRate + 1);
    
    if (newValue !== flowRate) {
      // Set flag to ignore our own update when it comes back
      localChangeRef.current = true;
      
      // Update local state immediately
      setFlowRate(newValue);
      
      // Send to server via WebSocket
      console.log("Sending flow rate update:", newValue);
      socketRef.current.emit("update_flow_rate", { flow_rate: newValue });
    }
  };
  
  // Decrease flow rate by 1
  const decreaseFlowRate = () => {
    if (!socketConnected) {
      console.error("Socket not connected - cannot update flow rate");
      return;
    }
    
    // Ensure we don't go below 0
    const newValue = Math.max(0, flowRate - 1);
    
    if (newValue !== flowRate) {
      // Set flag to ignore our own update when it comes back
      localChangeRef.current = true;
      
      // Update local state immediately
      setFlowRate(newValue);
      
      // Send to server via WebSocket
      console.log("Sending flow rate update:", newValue);
      socketRef.current.emit("update_flow_rate", { flow_rate: newValue });
    }
  };

  return (
    <div className="card col">
      <h1>Flow Rate Control</h1>
      <div className="flow-rate-simple">
        <div className="flow-rate-value">
          <span className="value">{flowRate}</span>
          <span className="unit">μL/min</span>
        </div>
        {socketConnected ? (
          <div className="flow-control-buttons">
            <button 
              className="flow-button" 
              onClick={decreaseFlowRate}
              disabled={procedureRunning}  // Disable during procedure
            >−</button>
            <button 
              className="flow-button" 
              onClick={increaseFlowRate}
              disabled={procedureRunning}  // Disable during procedure
            >+</button>
          </div>
        ) : (
          <div className="connection-error">
            Connecting to server...
          </div>
        )}
        {procedureRunning && (
          <div className="procedure-active-warning">
            Flow rate cannot be changed while procedure is running
          </div>
        )}
      </div>
    </div>
  );
}

export default FlowRateCard;