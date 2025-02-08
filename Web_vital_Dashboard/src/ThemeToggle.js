import React from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faSun, faMoon } from "@fortawesome/free-solid-svg-icons";

import "./ThemeToggle.css";

const ThemeToggle = () => {
  const toggleTheme = () => {
    document.body.classList.toggle("dark-mode");
  };

  return (
    <div className="toggle-container">
      <FontAwesomeIcon icon={faSun} className="sun-icon" />
      <label className="switch">
        <input type="checkbox" onChange={toggleTheme} />
        <span className="slider round small"></span>
      </label>
      <FontAwesomeIcon icon={faMoon} className="moon-icon" />
    </div>
  );
};

export default ThemeToggle;
