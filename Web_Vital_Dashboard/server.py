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

# Separate storage for synchronized variables - managed exclusively via WebSockets
FLOW_RATE = 0          # Flow rate in μL/min
DESIRED_VOL = 0        # Desired volume in μL
VOL_GIVEN = 0.0        # Current volume given in μL
PROCEDURE_RUNNING = False  # Procedure state (running or stopped)

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

    # Return sensor data along with current synchronized variables
    response = DATA_STORE.copy()
    response["flow_rate"] = FLOW_RATE
    response["desired_vol"] = DESIRED_VOL
    response["vol_given"] = VOL_GIVEN
    response["procedure_running"] = PROCEDURE_RUNNING
    
    return jsonify(response), 200
    
@app.route("/data", methods=["GET"])
def get_data():
    """
    React uses this endpoint to fetch sensor data
    """
    # Include all synchronized variables in the response
    response = DATA_STORE.copy()
    response["flow_rate"] = FLOW_RATE
    response["desired_vol"] = DESIRED_VOL
    response["vol_given"] = VOL_GIVEN
    response["procedure_running"] = PROCEDURE_RUNNING
    
    return jsonify(response), 200

# WebSocket event handlers
@socketio.on("connect")
def handle_connect():
    print(f"Client connected: {request.sid}")
    
    # Send current state to the newly connected client
    emit("flow_rate_update", {"flow_rate": FLOW_RATE})
    emit("desired_vol_update", {"desired_vol": DESIRED_VOL})
    emit("vol_given_update", {"vol_given": VOL_GIVEN})
    emit("procedure_state_update", {"running": PROCEDURE_RUNNING})

@socketio.on("disconnect")
def handle_disconnect():
    print(f"Client disconnected: {request.sid}")

@socketio.on("update_flow_rate")
def handle_flow_rate_update(data):
    """Handle flow rate updates from any client"""
    global FLOW_RATE
    try:
        new_flow_rate = int(round(float(data.get("flow_rate", FLOW_RATE))))
        # Ensure it's within valid range (0-30)
        new_flow_rate = max(0, min(30, new_flow_rate))
        
        # Update the global flow rate
        FLOW_RATE = new_flow_rate
        print(f"Flow rate updated via WebSocket to: {FLOW_RATE} μL/min by client {request.sid}")
        
        # Broadcast to all clients EXCEPT the sender
        emit("flow_rate_update", {"flow_rate": FLOW_RATE}, broadcast=True, include_self=False)
        return {"status": "success", "flow_rate": FLOW_RATE}
    except Exception as e:
        print(f"Error updating flow rate: {e}")
        return {"status": "error", "message": str(e)}

@socketio.on("update_desired_vol")
def handle_desired_vol_update(data):
    """Handle desired volume updates from any client"""
    global DESIRED_VOL
    try:
        new_desired_vol = int(round(float(data.get("desired_vol", DESIRED_VOL))))
        # Ensure it's within valid range (0-50)
        new_desired_vol = max(0, min(50, new_desired_vol))
        
        # Update the global desired volume
        DESIRED_VOL = new_desired_vol
        print(f"Desired volume updated via WebSocket to: {DESIRED_VOL} μL by client {request.sid}")
        
        # Broadcast to all clients EXCEPT the sender
        emit("desired_vol_update", {"desired_vol": DESIRED_VOL}, broadcast=True, include_self=False)
        return {"status": "success", "desired_vol": DESIRED_VOL}
    except Exception as e:
        print(f"Error updating desired volume: {e}")
        return {"status": "error", "message": str(e)}

@socketio.on("update_vol_given")
def handle_vol_given_update(data):
    """Handle volume given updates (typically from NORA.py)"""
    global VOL_GIVEN
    try:
        new_vol_given = float(data.get("vol_given", VOL_GIVEN))
        # Ensure it's not negative
        new_vol_given = max(0, new_vol_given)
        
        # Update the global volume given
        VOL_GIVEN = new_vol_given
        print(f"Volume given updated via WebSocket to: {VOL_GIVEN} μL by client {request.sid}")
        
        # Broadcast to all clients EXCEPT the sender
        emit("vol_given_update", {"vol_given": VOL_GIVEN}, broadcast=True, include_self=False)
        return {"status": "success", "vol_given": VOL_GIVEN}
    except Exception as e:
        print(f"Error updating volume given: {e}")
        return {"status": "error", "message": str(e)}

@socketio.on("procedure_state")
def handle_procedure_state_update(data):
    """Handle procedure state updates from any client"""
    global PROCEDURE_RUNNING
    try:
        new_state = bool(data.get("running", PROCEDURE_RUNNING))
        
        # Update the global procedure state
        PROCEDURE_RUNNING = new_state
        print(f"Procedure state updated via WebSocket to: {'Running' if PROCEDURE_RUNNING else 'Stopped'} by client {request.sid}")
        
        # Broadcast to all clients EXCEPT the sender
        emit("procedure_state_update", {"running": PROCEDURE_RUNNING}, broadcast=True, include_self=False)
        return {"status": "success", "running": PROCEDURE_RUNNING}
    except Exception as e:
        print(f"Error updating procedure state: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    print(f"Starting server on http://localhost:5000")
    print(f"WebSocket endpoint for variable synchronization at ws://localhost:5000")
    print(f"HTTP endpoints for sensor data at http://localhost:5000/data")
    socketio.run(app, host="0.0.0.0", port=5000, debug=True, allow_unsafe_werkzeug=True)