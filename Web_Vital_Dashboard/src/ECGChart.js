import React, { useEffect, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement);

function ECGChart({ data }) {
  const [chartOptions, setChartOptions] = useState(getOptions());

  function getOptions() {
    const isDarkMode = document.body.classList.contains("dark-mode");
    return {
      animation: false,
      scales: {
        x: {
          grid: {
            color: isDarkMode ? "#4A4A4A" : "#909090",
          },
          ticks: {
            color: isDarkMode ? "#FFF" : "#000",
          },
        },
        y: {
          grid: {
            color: isDarkMode ? "#4A4A4A" : "#909090",
          },
          ticks: {
            color: isDarkMode ? "#FFF" : "#000",
          },
        },
      },
    };
  }

  useEffect(() => {
    const bodyClassChangeHandler = () => {
      setChartOptions(getOptions());
    };

    document.body.addEventListener("change", bodyClassChangeHandler);

    return () => {
      document.body.removeEventListener("change", bodyClassChangeHandler);
    };
  }, []);

  // Convert ecgData to Chart.js data format
  const chartData = {
    labels: data.map((point) => (point.x == null ? "" : point.x)),
    datasets: [
      {
        data: data.map((point) => point.y),
        borderColor: "#BB0000",
        fill: false,
        pointRadius: 0,
      },
    ],
  };

  return <Line data={chartData} options={chartOptions} />;
}

export default ECGChart;
