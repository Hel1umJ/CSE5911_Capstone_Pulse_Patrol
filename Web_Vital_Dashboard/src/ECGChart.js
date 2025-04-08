import React, { useEffect, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Legend,
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement,Legend);

function ECGChart({ data }) {
  const [chartOptions, setChartOptions] = useState(getOptions());

  function getOptions() {
    const isDarkMode = document.body.classList.contains("dark-mode");
    return {
      animation: false,
      plugins: {
        legend: {
          display: true,
          position: 'top',
          labels: {
            usePointStyle: true,
          }
        },
      },
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
          min: 50,
          max: 110,
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
  const ChartData = {
    labels: data[0].map((point) => (point.x == null ? "" : point.x)),
    datasets: [
      {
        label:'Heart Rate(bpm)    ',
        data: data[0].map((point) => point.y),
        borderColor: '#BB0000',
        fill: false,
        pointStyle: 'circle',
        pointRadius: 7,
        //showLine: false,
        borderWidth: 0.5,
        pointBorderWidth: 2,
      },{
        label:'SpO2(%)    ',
        data: data[1].map((point) => point.y),
        borderColor: "#00008B",
        fill: false,
        pointStyle: 'crossRot',
        pointRadius: 10,
        //showLine: false,
        borderWidth: 0.5,
        pointBorderWidth: 2,
      },{
        label:'Dia    ',
        data: data[2].map((point) => point.y),
        borderColor: "#006400",
        fill: false,
        pointStyle: 'triangle',
        pointRadius: 10,
        //showLine: false,
        borderWidth: 0.5,
        pointBorderWidth: 2,
      },{
        label:'Sys    ',
        data: data[3].map((point) => point.y),
        borderColor: "#ffA500",
        fill: false,
        pointStyle: 'triangle',
        rotation: 180,
        pointRadius: 10,
        //showLine: false,
        borderWidth: 0.5,
        pointBorderWidth: 2,
      }
    ],
  };

  return <Line data={ChartData} options={chartOptions} />;

}

export default ECGChart;
