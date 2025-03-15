import time
import os
import json
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit

app = Flask(__name__, static_folder="build", static_url_path="")
CORS(app, resources={r"/*": {"origins": "*"}})
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# Store for sensor data
DATA_STORE = {
    "timestamp": 0.0,
    "heart_rate": 0,
    "spo2": 0,
    "bp_sys": 0,
    "bp_dia": 0
}

# Separate storage for flow rate - managed exclusively via WebSockets
FLOW_RATE = 0  # Initial flow rate (whole number)

@app.route("/nora", methods=["GET"])
def serve_react_app():
    """
    Anesthesiologist visits /nora to see webpage.
    """
    return send_from_directory(app.static_folder, "index.html")

@app.route("/data", methods=["POST"])
def data_endpoint():
    """
    Endpoint where the pi pushes sensor data
    Flow rate is handled separately via WebSockets
    """
    global DATA_STORE
    body = request.get_json()
    incoming_ts = float(body["timestamp"])
    incoming_hr = body.get("hr", None)
    incoming_spo2 = body.get("spo2", None)
    incoming_sys = body.get("bp_sys", None)
    incoming_dia = body.get("bp_dia", None)

    # Update sensor data 
    DATA_STORE["timestamp"] = incoming_ts
    if incoming_hr is not None:
        DATA_STORE["heart_rate"] = incoming_hr
    if incoming_spo2 is not None:
        DATA_STORE["spo2"] = incoming_spo2
    if incoming_sys is not None:
        DATA_STORE["bp_sys"] = incoming_sys
    if incoming_dia is not None:
        DATA_STORE["bp_dia"] = incoming_dia

    # Return sensor data along with current flow rate
    return jsonify({
        "timestamp": DATA_STORE["timestamp"],
        "heart_rate": DATA_STORE["heart_rate"],
        "spo2": DATA_STORE["spo2"],
        "bp_sys": DATA_STORE["bp_sys"],
        "bp_dia": DATA_STORE["bp_dia"],
        "flow_rate": FLOW_RATE,  # Include flow rate in response
    }), 200

@app.route("/data", methods=["GET"])
def get_data():
    """
    React uses this endpoint to fetch sensor data
    """
    # Include current flow rate in the response
    response = DATA_STORE.copy()
    response["flow_rate"] = FLOW_RATE
    return jsonify(response), 200

# WebSocket event handlers
@socketio.on("connect")
def handle_connect():
    print(f"Client connected: {request.sid}")
    # Send current flow rate to the newly connected client
    emit("flow_rate_update", {"flow_rate": FLOW_RATE})

@socketio.on("disconnect")
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on("update_flow_rate")
def handle_flow_rate_update(data):
    """Handle flow rate updates from any client"""
    global FLOW_RATE
    try:
        new_flow_rate = int(round(float(data.get("flow_rate", FLOW_RATE))))
        # Ensure it's within valid range
        new_flow_rate = max(0, min(30, new_flow_rate))
        
        # Update the global flow rate
        FLOW_RATE = new_flow_rate
        print(f"Flow rate updated via WebSocket to: {FLOW_RATE} by client {request.sid}")
        
        # Broadcast to all clients EXCEPT the sender
        emit("flow_rate_update", {"flow_rate": FLOW_RATE}, broadcast=True, include_self=False)
        return {"status": "success", "flow_rate": FLOW_RATE}
    except Exception as e:
        print(f"Error updating flow rate: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    print(f"Starting server on http://localhost:5000")
    print(f"WebSocket endpoint for flow rate synchronization at ws://localhost:5000")
    print(f"HTTP endpoints for sensor data at http://localhost:5000/data")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)