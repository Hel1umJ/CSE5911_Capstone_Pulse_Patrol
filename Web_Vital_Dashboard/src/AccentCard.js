import React from "react";
import { faker } from "@faker-js/faker";
import "./AccentCard.css";
import SmallSensorCard from "./SmallSensorCard";
import ThemeToggle from "./ThemeToggle";
import BloodPressureCard from "./BloodPressureCard";



function AccentCard() {
  const name = faker.person.fullName();
  const randomNumber = faker.number.int({ min: 10000000, max: 99999999 });
  const dob = faker.date.past().toLocaleDateString();

  return (
    <div className="lg-accent-card">
      <div className="user-info">
        <div className="text-column img-card">
          <img src={process.env.PUBLIC_URL + "/osuLogo.jpeg"} alt="OSU logo" />
        </div>
        <div className="text-column">
          <h1>{name}</h1>
          <div className="text-row">
            <h5 className="primary"># </h5>
            <h5>{randomNumber}</h5>
            <h5 className="primary">DOB </h5>
            <h5>{dob}</h5>
          </div>
        </div>
        
      </div>
      <div className="accent-col">
        <div className="accent-row">
          <SmallSensorCard
            iconName={"heart-pulse"}
            title={"Heart Rate"}
            path={"/heart_rate_val"}
            unit={"bpm"}
          />
        </div>
        <div className="accent-row">
          <SmallSensorCard
            iconName={"percent"}
            title={"SpO₂"}
            path={"/sp02_val"}
            unit={"%"}
          />
        </div>
        <div className="accent-row">
            <BloodPressureCard />
        </div>
      </div>
    </div>
  );
}

export default AccentCard;
