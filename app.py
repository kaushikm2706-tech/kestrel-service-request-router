"""Kestrel routing service.  Run:  python app.py   then open http://127.0.0.1:5000
No API key, no internet, no paid service is needed."""
import os
from flask import Flask, jsonify, request, render_template
from kestrel_router import model as M

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.environ.get("KESTREL_MODEL", os.path.join(HERE, "model.joblib"))

app = Flask(__name__)
_bundle = None


def bundle():
    global _bundle
    if _bundle is None:
        _bundle = M.load(MODEL_PATH)
    return _bundle


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    try:
        bundle()
        return jsonify(status="ok")
    except Exception as e:                      # model file missing -> say so politely, do not crash
        return jsonify(status="model_not_loaded", detail="Run: python -m kestrel_router.train ... (see README)"), 503


@app.post("/route")
def route():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not str(data.get("request_text", "")).strip():
        return jsonify(error="Send JSON like {\"request_text\": \"...\"}. "
                             "Optional: product_family, warranty_status, channel."), 400
    try:
        return jsonify(M.explain(bundle(), data))
    except FileNotFoundError:
        return jsonify(error="Model file not found. Run the training step in the README first."), 503


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)))
