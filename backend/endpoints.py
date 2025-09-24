from datetime import datetime, timezone

from flask import Blueprint, abort, jsonify, request, send_from_directory

from backend.app_config import RAINCZ_DIR, TEMPCZ_DIR

endpoints = Blueprint("endpoints", __name__)


def extract_timestamp(filename: str) -> datetime:
    ts_str = filename[:-4]
    return datetime.strptime(ts_str, "%Y-%m-%d_%H%M").replace(tzinfo=timezone.utc)


def parse_isoformat_z(dt_str: str) -> datetime:
    if dt_str.endswith("Z"):
        dt_str = dt_str.replace("Z", "+00:00")
    return datetime.fromisoformat(dt_str).astimezone(timezone.utc)


@endpoints.route("/api/raincz/list", methods=["GET"])
def rain_cz_list():
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

    for file_path in RAINCZ_DIR.glob("*.png"):
        filename = file_path.name
        try:
            ts = extract_timestamp(filename)
            if start_dt <= ts <= end_dt:
                results.append(
                    {"timestamp": ts.isoformat(), "url": f"/raincz/{filename}"}
                )
        except ValueError:
            continue

    results.sort(key=lambda x: x["timestamp"])
    return jsonify(results)


@endpoints.route("/api/raincz/<path:filename>")
def rain_cz_file(filename):
    try:
        return send_from_directory(str(RAINCZ_DIR), filename, mimetype="image/png")
    except FileNotFoundError:
        abort(404)


@endpoints.route("/api/tempcz/list", methods=["GET"])
def temp_cz_list():
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

    for file_path in TEMPCZ_DIR.glob("*.png"):
        filename = file_path.name
        try:
            ts = extract_timestamp(filename)
            if start_dt <= ts <= end_dt:
                results.append(
                    {"timestamp": ts.isoformat(), "url": f"/tempcz/{filename}"}
                )
        except ValueError:
            continue

    results.sort(key=lambda x: x["timestamp"])
    return jsonify(results)


@endpoints.route("/api/tempcz/<path:filename>")
def temp_cz_file(filename):
    try:
        return send_from_directory(str(TEMPCZ_DIR), filename, mimetype="image/png")
    except FileNotFoundError:
        abort(404)
