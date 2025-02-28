import React from "react";

class App extends React.Component {
  constructor(props) {
    super(props);

    this.state = {
      heart_rate: "N/A",
      spo2: "N/A",
      flow_rate: "N/A",
      bp_sys: "N/A",
      bp_dia: "N/A",
      timestamp: "N/A",
    };

    //keep a reference for this in this.self, inside callback update state with this
    this.self = this;
  }

  componentDidMount() {
    var self = this.self; // holds the reference to the component

    //callback function that executes every interval perdiod
    this.intervalId = setInterval(function() {
      //makes http request from endpoint
      fetch("/data") //Note: if full endpoint isnt provided, current endpoint of server is automatically prepended to URL
      .then(function(response) {
        return response.json();
      })
      .then(function(data) {
        self.setState({
          heart_rate: data.heart_rate || "N/A",
          spo2: data.spo2 || "N/A",
          flow_rate: data.flow_rate || "N/A",
          bp_sys: data.bp_sys || "N/A",
          bp_dia: data.bp_dia || "N/A",
          timestamp: data.timestamp || "N/A"
        });
      })
      .catch(function(error) {
        console.error("Error fetching /data:", error);
      });
    }, 1000);
  }


  componentWillUnmount() {
    clearInterval(this.intervalId);
  }

  render() {
    return (
      <div style={{ margin: "20px" }}>
        <h1>Simple Vitals Display (No Arrow Functions)</h1>
        <table border="1">
          <thead>
            <tr>
              <th>Heart Rate</th>
              <th>SpO₂</th>
              <th>Flow Rate</th>
              <th>Blood Pressure</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>{this.state.heart_rate}</td>
              <td>{this.state.spo2}</td>
              <td>{this.state.flow_rate}</td>
              <td>{this.state.bp_sys}/{this.state.bp_dia}</td>
              <td>{this.state.timestamp}</td>
            </tr>
          </tbody>
        </table>
      </div>
    );
  }
}

export default App;
