import React, { useState, useEffect } from "react";
import ECGChart from "./ECGChart";
import axios from "axios";

import "./GraphWrapper.css";

function GraphWrapper() {
  const [topGraphData, setTopGraphData] = useState([]);
  const [bottomGraphData, setBottomGraphData] = useState([]);

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
