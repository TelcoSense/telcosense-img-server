from datetime import datetime, timezone

from flask import Blueprint, abort, jsonify, request, send_from_directory

from backend.app_config import IMG_DIRS

endpoints = Blueprint("endpoints", __name__)


def extract_timestamp(filename: str) -> datetime:
    ts_str = filename[:-4]
    return datetime.strptime(ts_str, "%Y-%m-%d_%H%M").replace(tzinfo=timezone.utc)


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
            ts = extract_timestamp(file_path.name)
            if start_dt <= ts <= end_dt:
                results.append(
                    {
                        "timestamp": ts.isoformat(),
                        "url": f"/{datatype}/{file_path.name}",
                    }
                )
        except ValueError:
            continue

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
