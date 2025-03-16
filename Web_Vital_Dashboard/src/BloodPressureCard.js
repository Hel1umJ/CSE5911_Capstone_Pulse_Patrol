import React, { useState, useEffect } from "react";
import TextRow from "./TextRow";

function BloodPressureCard() {
  const [data, setData] = useState({ SYS: "...", DIA: "..." });

  // useEffect(() => {
  //   const interval = setInterval(async () => {
  //     const result = await axios("/blood_pressure_val");
  //     setData(result.data);
  //   }, 1000);

  //   return () => clearInterval(interval);
  // }, []);

  function displayValue(key) {
    if (data[key] !== "...") {
      return Math.round(data[key]).toString();
    }
    return "...";
  }

  return (
    <div className="card col">
      <h1>Blood Pressure</h1>
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
