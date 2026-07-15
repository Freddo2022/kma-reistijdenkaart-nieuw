from flask import send_from_directory
from flask import Flask, request, jsonify
import csv
import os

DTM_FILE = "dtm_pc4.csv"   # jouw bestand

# datastructuur { pc4_from: { pc4_to: {time_min, distance_km} } }
dtm = {}


def load_dtm(path):
    global dtm
    dtm.clear()

    with open(path, newline='', encoding='utf-8-sig') as f:
        # delimiter automatisch detecteren: ; of ,
        first_line = f.readline()
        delimiter = ";" if ";" in first_line else ","
        f.seek(0)

        reader = csv.DictReader(f, delimiter=delimiter)

        for row in reader:
            try:
                origin = row["pc4_from"].strip()
                dest = row["pc4_to"].strip()

                duration_s = float(row["duration_s"])      # seconden
                distance_m = float(row["distance_m"])      # meters

                time_min = round(duration_s / 60.0, 2)      # minuten
                distance_km = round(distance_m / 1000.0, 3) # km

            except Exception as e:
                print("Rij overgeslagen:", row, e)
                continue

            if origin not in dtm:
                dtm[origin] = {}

            dtm[origin][dest] = {
                "time_min": time_min,
                "distance_km": distance_km
            }


# laad de data bij start
load_dtm(DTM_FILE)
print(f"DTM geladen: {len(dtm)} origins")

app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/dtm")
def get_dtm():
    origin = request.args.get("origin")
    if not origin:
        return jsonify({"error": "origin parameter required"}), 400

    origin = origin.strip()

    if origin not in dtm:
        return jsonify({"error": f"origin {origin} not found"}), 404

    # maak een mooie lijst
    result = [
        {
            "dest_pc4": dest,
            "time_min": values["time_min"],
            "distance_km": values["distance_km"]
        }
        for dest, values in dtm[origin].items()
    ]

    return jsonify({
        "origin_pc4": origin,
        "count": len(result),
        "results": result
    })

@app.route("/origins")
def get_origins():
    origins = sorted(list(dtm.keys()))
    return jsonify({"origins": origins})

@app.route("/geo/<path:filename>")
def serve_geo(filename):
    return send_from_directory("static/geo", filename)



if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    print(f"KmA DTM backend draait op http://localhost:{port}")
    app.run(host="0.0.0.0", port=port)
