import React, { useState, useEffect, useRef } from "react";
import { io } from "socket.io-client";
import "./FlowRateCard.css";


// CURRENTLY NOT BEING USED
// CODE TRANSFERED TO FLOWRATECONTROLSCARD.JS
// KEEPING IN CASE FUNCTIONALITY IS BROKEN

function ProcedureControlCard() {
  const [procedureRunning, setProcedureRunning] = useState(false);
  const [volumeGiven, setVolumeGiven] = useState(0);
  const [desiredVolume, setDesiredVolume] = useState(0);
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
    
    // Handler for procedure state updates
    socket.on("procedure_state_update", (data) => {
      console.log("Received procedure state update:", data);
      
      // Only update if it wasn't a local change
      if (!localChangeRef.current) {
        setProcedureRunning(data.running);
        
        // If procedure is starting, reset volume given
        if (data.running) {
          setVolumeGiven(0);
        }
      } else {
        // Reset the flag
        localChangeRef.current = false;
      }
    });
    
    // Handler for volume given updates
    socket.on("vol_given_update", (data) => {
      console.log("Received volume given update:", data);
      
      // Always update volume given when it comes from server
      if (data.vol_given !== undefined) {
        const newVol = parseFloat(data.vol_given);
        console.log("Setting volume given to:", newVol);
        setVolumeGiven(newVol);
      }
    });
    
    // Handler for desired volume updates
    socket.on("desired_vol_update", (data) => {
      console.log("Received desired volume update:", data);
      
      // Only update if it wasn't a local change
      if (!localChangeRef.current) {
        setDesiredVolume(data.desired_vol);
      } else {
        // Reset the flag
        localChangeRef.current = false;
      }
    });
    
    // Initial data fetch
    const fetchInitialData = async () => {
      try {
        const response = await fetch("/data");
        const data = await response.json();
        
        if (data) {
          setProcedureRunning(data.procedure_running || false);
          setDesiredVolume(data.desired_vol || 0);
          
          // Explicitly handle volume given with proper parsing
          if (data.vol_given !== undefined) {
            const newVol = parseFloat(data.vol_given);
            console.log("Initial volume given:", newVol);
            setVolumeGiven(newVol);
          }
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
  
  // Toggle procedure running state
  const toggleProcedure = () => {
    if (!socketConnected) {
      console.error("Socket not connected - cannot toggle procedure");
      return;
    }
    
    // Set flag to ignore our own update when it comes back
    localChangeRef.current = true;
    
    // Update local state immediately
    setProcedureRunning(!procedureRunning);
    
    // If starting procedure, reset volume given
    if (!procedureRunning) {
      setVolumeGiven(0);
    }
    
    // Send to server via WebSocket
    console.log("Sending procedure state update:", !procedureRunning);
    socketRef.current.emit("procedure_state", { running: !procedureRunning });
  };
  
  // Increase desired volume
  const increaseDesiredVolume = () => {
    if (!socketConnected) {
      console.error("Socket not connected - cannot update volume");
      return;
    }
    
    // Ensure we don't exceed maximum volume (50μL)
    const newValue = Math.min(50, desiredVolume + 1);
    
    if (newValue !== desiredVolume) {
      // Set flag to ignore our own update when it comes back
      localChangeRef.current = true;
      
      // Update local state immediately
      setDesiredVolume(newValue);
      
      // Send to server via WebSocket
      console.log("Sending desired volume update:", newValue);
      socketRef.current.emit("update_desired_vol", { desired_vol: newValue });
    }
  };
  
  // Decrease desired volume
  const decreaseDesiredVolume = () => {
    if (!socketConnected) {
      console.error("Socket not connected - cannot update volume");
      return;
    }
    
    // Ensure we don't go below 0
    const newValue = Math.max(0, desiredVolume - 1);
    
    if (newValue !== desiredVolume) {
      // Set flag to ignore our own update when it comes back
      localChangeRef.current = true;
      
      // Update local state immediately
      setDesiredVolume(newValue);
      
      // Send to server via WebSocket
      console.log("Sending desired volume update:", newValue);
      socketRef.current.emit("update_desired_vol", { desired_vol: newValue });
    }
  };
  
  // Calculate progress percentage
  const progressPercentage = desiredVolume > 0 
    ? Math.min(100, (volumeGiven / desiredVolume) * 100) 
    : 0;

  return (
    <div className="procedure-control-container">
      {/* Desired Volume Control */}
      <div className="card col">
        <h1>Desired Volume</h1>
        <div className="flow-rate-simple">
          <div className="flow-rate-value">
            <span className="value">{desiredVolume}</span>
            <span className="unit">μL</span>
          </div>
          {socketConnected ? (
            <div className="flow-control-buttons">
              <button 
                className="flow-button" 
                onClick={decreaseDesiredVolume}
                disabled={procedureRunning}
              >−</button>
              <button 
                className="flow-button" 
                onClick={increaseDesiredVolume}
                disabled={procedureRunning}
              >+</button>
            </div>
          ) : (
            <div className="connection-error">
              Connecting to server...
            </div>
          )}
        </div>
      </div>
      
      {/* Procedure Control */}
      <div className="card col">
        <h1>Procedure Control</h1>
        <div className="procedure-status">
          <div className="status-indicator">
            Status: 
            <span className={procedureRunning ? "status-running" : "status-stopped"}>
              {procedureRunning ? " Running" : " Stopped"}
            </span>
          </div>
          
          <div className="volume-progress">
            <div className="volume-info">
              <span>Volume Given: {volumeGiven.toFixed(2)} / {desiredVolume} μL</span>
            </div>
            <div className="progress-bar-container">
              <div 
                className="progress-bar-fill" 
                style={{ width: `${progressPercentage}%` }}
              ></div>
            </div>
          </div>
          
          {socketConnected ? (
            <button 
              className={`procedure-button ${procedureRunning ? 'stop' : 'start'}`}
              onClick={toggleProcedure}
            >
              {procedureRunning ? "Stop Procedure" : "Start Procedure"}
            </button>
          ) : (
            <div className="connection-error">
              Connecting to server...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ProcedureControlCard;