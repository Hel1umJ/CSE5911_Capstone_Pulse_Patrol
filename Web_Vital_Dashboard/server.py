import time
import os
from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="build", static_url_path="")

DATA_STORE = {
    "flow_rate": 0.0,
    "timestamp": 0.0,
    "heart_rate": 0,
    "spo2": 0,
    "bp_sys": 0,
    "bp_dia": 0
}

@app.route("/nora", methods=["GET"])
def serve_react_app():
    """
    Anesthesiologist visits /nora to see webpage.
    """
    return send_from_directory(app.static_folder, "index.html")

@app.route("/data", methods=["POST"])
def data_endpoint():
    """
    Endpoint where both pi and server push their data to
    """
    body = request.get_json()
    incoming_ts = float(body["timestamp"])
    incoming_flow = float(body.get("flow_rate", 0.0))
    incoming_hr = body.get("hr", None)
    incoming_spo2 = body.get("spo2", None)
    incoming_sys = body.get("bp_sys", None)
    incoming_dia = body.get("bp_dia", None)

    server_ts = DATA_STORE["timestamp"]

    if incoming_ts > server_ts:
        #Pi's data is newer, update
        DATA_STORE["timestamp"] = incoming_ts
        DATA_STORE["flow_rate"] = incoming_flow
        if incoming_hr is not None:
            DATA_STORE["heart_rate"] = incoming_hr
        if incoming_spo2 is not None:
            DATA_STORE["spo2"] = incoming_spo2
        if incoming_sys is not None:
            DATA_STORE["bp_sys"] = incoming_sys
        if incoming_dia is not None:
            DATA_STORE["bp_dia"] = incoming_dia

    return jsonify({
        "timestamp": DATA_STORE["timestamp"],
        "flow_rate": DATA_STORE["flow_rate"],
        "heart_rate": DATA_STORE["heart_rate"],
        "spo2": DATA_STORE["spo2"],
        "bp_sys": DATA_STORE["bp_sys"],
        "bp_dia": DATA_STORE["bp_dia"],
    }), 200

@app.route("/data", methods=["GET"])
def get_data():
    """
    React uses this endpoint to fetch data for display
    """
    return jsonify(DATA_STORE), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
