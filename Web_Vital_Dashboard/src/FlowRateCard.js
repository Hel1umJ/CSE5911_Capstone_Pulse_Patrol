import React, { useEffect, useState, useRef } from "react";
import axios from "axios";
import { io } from "socket.io-client";
import "./FlowRateCard.css";

function FlowRateCard() {
  const [flowRate, setFlowRate] = useState(0);
  const [socketConnected, setSocketConnected] = useState(false);
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
    
    // Initial data fetch to get current flow rate
    const fetchInitialData = async () => {
      try {
        const response = await axios.get("/data");
        if (response.data && response.data.flow_rate !== undefined) {
          setFlowRate(response.data.flow_rate);
        }
      } catch (error) {
        console.error("Error fetching initial flow rate:", error);
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
            <button className="flow-button" onClick={decreaseFlowRate}>−</button>
            <button className="flow-button" onClick={increaseFlowRate}>+</button>
          </div>
        ) : (
          <div className="connection-error">
            Connecting to server...
          </div>
        )}
      </div>
    </div>
  );
}

export default FlowRateCard;