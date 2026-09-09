import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from inference import load_symptom_alias_map, load_symptom_name_map, predict_with_details
from labels import load_disease_name_map


DEFAULT_MODEL_PATH = Path("models/symptom_disease_41_nb.json")


def load_model(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class DiseasePredictHandler(BaseHTTPRequestHandler):
    model = None
    disease_name_map = None
    symptom_alias_map = None
    symptom_name_map = None

    def log_message(self, format, *args):
        return

    def send_json(self, status_code, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_json(200, {"ok": True})

    def do_GET(self):
        parsed_url = urlparse(self.path)
        if parsed_url.path == "/health":
            self.send_json(200, {"status": "ok"})
            return
        if parsed_url.path != "/predict":
            self.send_json(404, {"error": "not_found"})
            return

        query = parse_qs(parsed_url.query)
        symptoms = query.get("symptoms", [""])[0]
        details = predict_with_details(
            self.model,
            symptoms,
            disease_name_map=self.disease_name_map,
            symptom_alias_map=self.symptom_alias_map,
            symptom_name_map=self.symptom_name_map,
        )
        if not details["disease"]:
            self.send_json(400, {"error": "symptoms_required"})
            return
        if query.get("details", ["0"])[0] in {"1", "true", "yes"}:
            self.send_json(200, details)
            return
        self.send_json(200, {"disease": details["disease"]})

    def do_POST(self):
        if urlparse(self.path).path != "/predict":
            self.send_json(404, {"error": "not_found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw_body or "{}")
        except json.JSONDecodeError:
            self.send_json(400, {"error": "invalid_json"})
            return

        details = predict_with_details(
            self.model,
            payload.get("symptoms"),
            disease_name_map=self.disease_name_map,
            symptom_alias_map=self.symptom_alias_map,
            symptom_name_map=self.symptom_name_map,
        )
        if not details["disease"]:
            self.send_json(400, {"error": "symptoms_required"})
            return
        if payload.get("details") is True:
            self.send_json(200, details)
            return
        self.send_json(200, {"disease": details["disease"]})


def main():
    parser = argparse.ArgumentParser(description="HTTP API for disease name prediction.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5002)
    parser.add_argument("--model", default=str(DEFAULT_MODEL_PATH))
    parser.add_argument("--english", action="store_true", help="Return original English disease labels")
    args = parser.parse_args()

    DiseasePredictHandler.model = load_model(args.model)
    DiseasePredictHandler.disease_name_map = {} if args.english else load_disease_name_map()
    DiseasePredictHandler.symptom_alias_map = load_symptom_alias_map()
    DiseasePredictHandler.symptom_name_map = load_symptom_name_map()
    server = ThreadingHTTPServer((args.host, args.port), DiseasePredictHandler)
    print(f"listening=http://{args.host}:{args.port}")
    print("endpoint=POST /predict")
    server.serve_forever()


if __name__ == "__main__":
    main()
