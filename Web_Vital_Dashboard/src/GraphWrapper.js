import React, { useState, useEffect } from "react";
import ECGChart from "./ECGChart";
import axios from "axios";

import "./GraphWrapper.css";

function GraphWrapper() {
  const [topGraphData, setTopGraphData] = useState([]);
  const [bottomGraphData, setBottomGraphData] = useState([]);

  useEffect(() => {
    const interval = setInterval(() => {
      // Generate random data for topGraphData
      const newTopData = Array.from({ length: 50 }, (_, i) => ({
        x: i,
        y: Math.random() * 2 - 1,
      }));

      // Generate random data for bottomGraphData
      const newBottomData = Array.from({ length: 50 }, (_, i) => ({
        x: i,
        y: Math.random() * 2 - 1,
      }));

      setTopGraphData(newTopData);
      setBottomGraphData(newBottomData);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    function getLastValues(array) {
      const xWidth = 200;
      if (array.length > xWidth) {
        return array.slice(array.length - xWidth);
      } else {
        return array;
      }
    }

    // const interval = setInterval(async () => {
    //   const result = await axios("/ecg_data");
    //   const slicedArray = getLastValues(result.data);
    //   setTopGraphData((_) => {
    //     return slicedArray.map((point) => ({ x: null, y: point["A0"] }));
    //   });
    //   setBottomGraphData((_) => {
    //     return slicedArray.map((point) => ({ x: null, y: point['A5'] }));
    //   });
    // }, 300);

    //return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <ECGChart data={topGraphData} />
      <ECGChart data={bottomGraphData} />
    </div>
  );
}

export default GraphWrapper;
