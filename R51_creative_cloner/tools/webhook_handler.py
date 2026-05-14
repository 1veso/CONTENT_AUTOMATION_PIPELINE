"""
R51 ingest webhook — Flask server that fronts `ingest_url()`.

n8n (or any other automation) POSTs to /ingest with the source URL; this
handler runs yt-dlp/camofox, uploads to R2, writes Airtable, and returns
the R2 URL + record id.

Endpoints:
  GET  /health     → {"status": "ok"} for cheap probes
  POST /ingest     → JSON {url, project_name?, brand?} → ingest_url() result

Run:
  python -m tools.webhook_handler                       # port 8765
  PORT=9000 python -m tools.webhook_handler             # override port
"""

import os
import sys
import traceback

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass

from flask import Flask, jsonify, request

from . import ingest as ingest_mod


app = Flask(__name__)


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/ingest")
def ingest_endpoint():
    payload = request.get_json(silent=True) or {}
    url = payload.get("url")
    if not url:
        return jsonify({"status": "error", "error": "missing 'url'"}), 400
    try:
        result = ingest_mod.ingest_url(
            url,
            project_name=payload.get("project_name"),
            brand=payload.get("brand"),
        )
        return jsonify(result), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"status": "error", "error": str(e)}), 500


def main():
    port = int(os.environ.get("PORT", "8765"))
    host = os.environ.get("HOST", "0.0.0.0")
    app.run(host=host, port=port, debug=False)


if __name__ == "__main__":
    main()
