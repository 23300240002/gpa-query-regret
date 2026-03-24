from __future__ import annotations

import threading
import uuid
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from calculate import (
    ValidationError,
    calculate_weighted_gpa,
    default_included,
    format_decimal,
    get_semesters,
    load_courses_from_csv_bytes,
)


BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__, template_folder="templates")

# 轻量内存存储：单机本地运行场景足够。
_DATASETS: dict[str, list] = {}


def _course_id(course) -> str:
    return f"{course.semester}::{course.name}"


def _build_course_rows(scoped_courses, include_overrides: dict[str, bool]):
    rows = []
    for c in scoped_courses:
        cid = _course_id(c)
        base_included = default_included(c)
        included = include_overrides.get(cid, base_included)

        if included and c.gpa is None:
            raise ValidationError(f"课程【{c.name}】没有绩点，无法手动计入。")

        if included and base_included:
            status = "计入"
        elif included and not base_included:
            status = "计入(手动切换)"
        elif not included and base_included:
            status = "不计入(手动切换)"
        elif c.grade in {"P", "NP", "F"}:
            status = f"不计入({c.grade})"
        else:
            status = "不计入(绩点缺失)"

        rows.append(
            {
                "course_id": cid,
                "name": c.name,
                "semester": c.semester,
                "course_type": c.course_type,
                "credit": str(c.credit),
                "grade": c.grade,
                "gpa": "" if c.gpa is None else str(c.gpa),
                "status": status,
                "included": included,
                "default_included": base_included,
                "remark": c.remark,
            }
        )
    return rows


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/upload")
def api_upload():
    upload = request.files.get("file")
    if upload is None:
        return jsonify({"ok": False, "error": "未检测到文件，请选择 CSV 文件上传。"}), 400

    filename = (upload.filename or "").strip()
    if not filename.lower().endswith(".csv"):
        return jsonify({"ok": False, "error": "仅支持 .csv 文件。"}), 400

    raw = upload.read()
    if not raw:
        return jsonify({"ok": False, "error": "上传文件为空。"}), 400

    try:
        courses = load_courses_from_csv_bytes(raw)
    except (ValidationError, ValueError) as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    dataset_id = uuid.uuid4().hex
    _DATASETS[dataset_id] = courses

    return jsonify(
        {
            "ok": True,
            "dataset_id": dataset_id,
            "filename": filename,
            "semesters": get_semesters(courses),
            "course_count": len(courses),
        }
    )


@app.post("/api/calculate")
def api_calculate():
    data = request.get_json(silent=True) or {}
    dataset_id = str(data.get("dataset_id") or "").strip()
    if dataset_id == "" or dataset_id not in _DATASETS:
        return jsonify({"ok": False, "error": "请先上传有效 CSV 文件。"}), 400

    courses = _DATASETS[dataset_id]
    all_semesters = get_semesters(courses)

    selected_semesters = data.get("semesters") or all_semesters
    selected_semesters = [s for s in selected_semesters if s in all_semesters]
    if not selected_semesters:
        return jsonify({"ok": False, "error": "请选择至少一个有效学期。"}), 400

    scoped_courses = [c for c in courses if c.semester in selected_semesters]

    include_overrides = data.get("include_overrides") or {}
    if not isinstance(include_overrides, dict):
        return jsonify({"ok": False, "error": "include_overrides 字段必须是对象。"}), 400

    valid_ids = {_course_id(c) for c in scoped_courses}
    normalized: dict[str, bool] = {}
    for key, value in include_overrides.items():
        if key not in valid_ids:
            continue
        if not isinstance(value, bool):
            return jsonify({"ok": False, "error": f"课程切换项 {key} 的值必须为布尔值。"}), 400
        normalized[key] = value

    try:
        total_credits, avg_gpa = calculate_weighted_gpa(scoped_courses, normalized)
        rows = _build_course_rows(scoped_courses, normalized)
    except ValidationError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400

    return jsonify(
        {
            "ok": True,
            "selected_semesters": selected_semesters,
            "total_credits": str(total_credits),
            "average_gpa": format_decimal(avg_gpa),
            "courses": rows,
            "course_count": len(rows),
        }
    )


@app.get("/api/health")
def api_health():
    return jsonify({"ok": True})


@app.get("/favicon.ico")
def favicon():
    return ("", 204)


def _open_browser() -> None:
    webbrowser.open("http://127.0.0.1:8000")


if __name__ == "__main__":
    timer = threading.Timer(0.8, _open_browser)
    timer.start()
    app.run(host="127.0.0.1", port=8000, debug=False)
