import React, { useState, useEffect, useRef } from "react";
import ECGChart from "./ECGChart";
import axios from "axios";

import "./GraphWrapper.css";

function GraphWrapper() {
  // We'll keep a single array of heart rate data points
  const [heartRateData, setHeartRateData] = useState([]);
  const [SPO2RateData, setSPO2Data] = useState([]);
  const [bpDiaData, setBpDiaData] = useState([]);
  const [bpSysData, setBpSysData] = useState([]);

  const dataPointsRef = useRef(0); // To keep track of total points for x-axis
  
  // Maximum number of points to display on graph
  const MAX_POINTS = 50;

  useEffect(() => {
    // Start with some initial empty data
    const initialData = Array.from({ length: MAX_POINTS }, (_, i) => ({
      x: i,
      y: null // null will not be plotted
    }));
    //setHeartRateData(initialData);
    //setSPO2Data(initialData);
    
    // Function to fetch the latest data
    const fetchData = async () => {
      try {
        const response = await axios.get("http://localhost:5000/data");
        console.log("Response: ", response);
        
        // Extract heart rate from response
        const newHeartRate = response.data.heart_rate;
        const newSpo2Rate = response.data.spo2;
        const newBpDiaRate = response.data.bp_dia;
        const newBpSysRate = response.data.bp_sys;

        
        // Create a new data point
        const newHeartRatePoint = {
          x: dataPointsRef.current,
          y: newHeartRate
        };

        const newSP02Point = {
          x: dataPointsRef.current,
          y: newSpo2Rate
        };

        const newBpDiaPoint = {
          x: dataPointsRef.current,
          y: newBpDiaRate
        };

        const newBpSysPoint = {
          x: dataPointsRef.current,
          y: newBpSysRate
        };
        
        // Increment our counter for the next point
        dataPointsRef.current += 1;
        
        // Update state by adding the new point and keeping only the latest MAX_POINTS
        setHeartRateData(prevData => {
          // Add the new point
          const updatedData = [...prevData, newHeartRatePoint];
          
          // If we have more than MAX_POINTS, remove oldest points
          if (updatedData.length > MAX_POINTS) {
            return updatedData.slice(updatedData.length - MAX_POINTS);
          }
          
          return updatedData;
        });

        setSPO2Data(prevData => {
          // Add the new point
          const updatedData = [...prevData, newSP02Point];
          
          // If we have more than MAX_POINTS, remove oldest points
          if (updatedData.length > MAX_POINTS) {
            return updatedData.slice(updatedData.length - MAX_POINTS);
          }
          
          return updatedData;
        });

        setBpDiaData(prevData => {
          // Add the new point
          const updatedData = [...prevData, newBpDiaPoint];
          
          // If we have more than MAX_POINTS, remove oldest points
          if (updatedData.length > MAX_POINTS) {
            return updatedData.slice(updatedData.length - MAX_POINTS);
          }
          
          return updatedData;
        });

        setBpSysData(prevData => {
          // Add the new point
          const updatedData = [...prevData, newBpSysPoint];
          
          // If we have more than MAX_POINTS, remove oldest points
          if (updatedData.length > MAX_POINTS) {
            return updatedData.slice(updatedData.length - MAX_POINTS);
          }
          
          return updatedData;
        });
      } catch (error) {
        console.error("Error fetching data:", error);
      }
    };

    // Set up polling interval (every 1 second)
    const interval = setInterval(fetchData, 10000);
    
    // Initial fetch
    fetchData();

    // Clean up interval on component unmount
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <ECGChart data={[heartRateData, SPO2RateData, bpDiaData, bpSysData]} />
    </div>
  );
}

export default GraphWrapper;