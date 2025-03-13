import React, { useEffect, useState } from "react";
import PureKnob from "./PureKnob.js";
import axios from "axios";

import "./FlowRateCard.css";

function FlowRateCard() {
  const [knob, setKnob] = useState(null);
  const [knobValue, setKnobValue] = useState(0);
  const [setValue, setSetValue] = useState(null);
  const [isDarkMode, setIsDarkMode] = useState(
    document.body.classList.contains("dark-mode")
  );

  useEffect(() => {
    const bodyClassChangeHandler = () => {
      if (knob != null) {
        setKnobValue(knob.getValue());
      }
      setIsDarkMode(document.body.classList.contains("dark-mode"));
    };

    document.body.addEventListener("change", bodyClassChangeHandler);

    return () => {
      document.body.removeEventListener("change", bodyClassChangeHandler);
    };
  }, [knob]);

  useEffect(() => {
    const pureKnob = new PureKnob();
    const newKnob = pureKnob.createKnob(175, 150);
    newKnob.setProperty("angleStart", -0.63 * Math.PI);
    newKnob.setProperty("angleEnd", 0.63 * Math.PI);
    newKnob.setProperty("colorFG", isDarkMode ? "#FFF" : "#000");
    newKnob.setProperty("colorBG", isDarkMode ? "#4A4A4A" : "#909090");
    newKnob.setProperty("trackWidth", 0.3);
    newKnob.setProperty("valMin", 0);
    newKnob.setProperty("valMax", 100);
    newKnob.setValue(knobValue);
    const node = newKnob.node();
    setKnob(newKnob);
    const elem = document.getElementById("knob");
    elem.innerHTML = "";
    elem.appendChild(node);
  }, [isDarkMode, knobValue]);

  function changeValueBy(n) {
    let oldValue = knob.getValue();
    knob.setValue(oldValue + n);
  }

  function confirmValue() {
    // const data = knob.getValue().toString();
    // console.log("Set value: " + data);
    // axios.post(
    //   "/motor_instructions",
    //   { value: data },
    //   { headers: { "Content-Type": "application/json" } }
    // );
    // setSetValue(knob.getValue());
  }

  function stopMotor() {
    // knob.setValue(0);
    // const data = "S";
    // axios.post(
    //   "/motor_instructions",
    //   { value: data },
    //   { headers: { "Content-Type": "application/json" } }
    // );
    // console.log("Ser value: " + data);
    // setSetValue(null);
  }

  function displaySetValue() {
    if (setValue == null) {
      return "Stopped";
    } else if (setValue === -1) {
      return "Reversing";
    }
    const unitVal = 0.45 + 0.01 * setValue;
    return setValue + " (" + unitVal.toFixed(2) + " mL/s)";
  }

  function reverse() {
    // knob.setValue(0);
    // const data = "B";
    // axios.post(
    //   "/motor_instructions",
    //   { value: data },
    //   { headers: { "Content-Type": "application/json" } }
    // );
    // console.log("Ser value: " + data);
    // setSetValue(-1);
  }

  return (
    <div className="card lg">
      <h1>Flow Rate</h1>
      <div className="center">
        <button className="rev-btn" onClick={() => reverse()}>
          &#x23EA;
        </button>
        <div id="knob"></div>
        <div className="btn-row">
          <button onClick={() => changeValueBy(-5)}>-5</button>
          <button onClick={() => changeValueBy(-1)}>-1</button>
          <button onClick={() => stopMotor()}>&#x23F9;</button>
          <button onClick={() => changeValueBy(1)}>+1</button>
          <button onClick={() => changeValueBy(5)}>+5</button>
        </div>
        <button className="confirm-btn" onClick={() => confirmValue()}>
          Confirm
        </button>
        <h2>Set Value: {displaySetValue()}</h2>
      </div>
    </div>
  );
}

export default FlowRateCard;
