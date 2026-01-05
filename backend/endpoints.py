import json
from datetime import datetime, timezone
from pathlib import Path

from flask import Blueprint, abort, jsonify, request, send_from_directory

from backend.app_config import IMG_DIRS

endpoints = Blueprint("endpoints", __name__)

JSON_DIR = Path("../telcotemp-meteo-cli/outputs_json").resolve()  # ← adjust if needed


def extract_timestamp_and_score(filename: str):
    stem = filename[:-4]
    parts = stem.split("_")
    # old: ["YYYY-MM-DD", "HHMM"]
    if len(parts) == 2:
        ts = datetime.strptime(stem, "%Y-%m-%d_%H%M").replace(tzinfo=timezone.utc)
        return ts, None
    # new: ["YYYY-MM-DD", "HHMM", "<score>"]
    if len(parts) >= 3:
        ts_str = "_".join(parts[:2])  # YYYY-MM-DD_HHMM
        ts = datetime.strptime(ts_str, "%Y-%m-%d_%H%M").replace(tzinfo=timezone.utc)
        score = None
        try:
            score = float(parts[2])
        except ValueError:
            score = None
        return ts, score
    raise ValueError(f"Unrecognized filename format: {filename}")


def extract_json_timestamp(filename: str) -> datetime:
    stem = filename[:-5]  # remove ".json"
    return datetime.strptime(stem, "%Y-%m-%d_%H%M").replace(tzinfo=timezone.utc)


def parse_isoformat_z(dt_str: str) -> datetime:
    if dt_str.endswith("Z"):
        dt_str = dt_str.replace("Z", "+00:00")
    return datetime.fromisoformat(dt_str).astimezone(timezone.utc)


@endpoints.route("/api/<datatype>/list", methods=["GET"])
def list_files(datatype):
    directory = IMG_DIRS.get(datatype)
    if not directory:
        abort(404, f"Unknown data type '{datatype}'")
    start_str = request.args.get("start")
    end_str = request.args.get("end")
    if not start_str or not end_str:
        abort(400, "'start' and 'end' query parameters are required (ISO format)")
    try:
        start_dt = parse_isoformat_z(start_str)
        end_dt = parse_isoformat_z(end_str)
    except ValueError:
        abort(400, "Invalid ISO datetime format")
    results = []
    for file_path in directory.glob("*.png"):
        try:
            ts, rain_score = extract_timestamp_and_score(file_path.name)
        except ValueError:
            continue
        if start_dt <= ts <= end_dt:
            item = {
                "timestamp": ts.isoformat(),
                "url": f"/{datatype}/{file_path.name}",
            }
            # include only when present
            if rain_score is not None:
                item["rain_score"] = rain_score
            results.append(item)
    results.sort(key=lambda x: x["timestamp"])
    return jsonify(results)


@endpoints.route("/api/<datatype>/<path:filename>")
def serve_file(datatype, filename):
    directory = IMG_DIRS.get(datatype)
    if not directory:
        abort(404, f"Unknown data type '{datatype}'")
    try:
        return send_from_directory(str(directory), filename, mimetype="image/png")
    except FileNotFoundError:
        abort(404)


@endpoints.route("/api/drywet", methods=["GET"])
def list_frames():
    start_str = request.args.get("start")
    end_str = request.args.get("end")
    if not start_str or not end_str:
        abort(400, "'start' and 'end' query parameters are required (ISO format)")
    try:
        start_dt = parse_isoformat_z(start_str)
        end_dt = parse_isoformat_z(end_str)
    except ValueError:
        abort(400, "Invalid ISO datetime format")
    results = []
    for file_path in JSON_DIR.glob("*.json"):
        try:
            ts = extract_json_timestamp(file_path.name)
        except ValueError:
            continue
        if start_dt <= ts <= end_dt:
            try:
                with file_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError):
                continue
            results.append(data)
    results.sort(key=lambda x: x.get("utc", ""))
    return jsonify(results)
