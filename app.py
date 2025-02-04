from flask import Flask, jsonify
import json

app = Flask(__name__)

@app.route('/api/tsa-wait-times', methods=['GET'])
def get_tsa_wait_times():
    """API endpoint to fetch TSA wait times."""
    try:
        with open("tsa_wait_times.json", "r") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": "Could not fetch data", "details": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
