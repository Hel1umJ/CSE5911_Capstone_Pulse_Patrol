import React, { useState, useEffect, useRef } from "react";
import ECGChart from "./ECGChart";
import axios from "axios";

import "./GraphWrapper.css";

function GraphWrapper() {
  // We'll keep a single array of heart rate data points
  const [heartRateData, setHeartRateData] = useState([]);
  const dataPointsRef = useRef(0); // To keep track of total points for x-axis
  
  // Maximum number of points to display on graph
  const MAX_POINTS = 50;

  useEffect(() => {
    // Start with some initial empty data
    const initialData = Array.from({ length: MAX_POINTS }, (_, i) => ({
      x: i,
      y: null // null will not be plotted
    }));
    setHeartRateData(initialData);
    
    // Function to fetch the latest data
    const fetchData = async () => {
      try {
        const response = await axios.get("/data");
        console.log("Response: ", response);
        
        // Extract heart rate from response
        const newHeartRate = response.data.heart_rate;
        
        // Create a new data point
        const newPoint = {
          x: dataPointsRef.current,
          y: newHeartRate
        };
        
        // Increment our counter for the next point
        dataPointsRef.current += 1;
        
        // Update state by adding the new point and keeping only the latest MAX_POINTS
        setHeartRateData(prevData => {
          // Add the new point
          const updatedData = [...prevData, newPoint];
          
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
    const interval = setInterval(fetchData, 1000);
    
    // Initial fetch
    fetchData();

    // Clean up interval on component unmount
    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <ECGChart data={heartRateData} />
    </div>
  );
}

export default GraphWrapper;