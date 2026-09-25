"""Independent degree requirement graph closure simulator — not hotel inventory allocation."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def audit_date(meta: dict) -> str:
    override = os.environ.get("TB3_AUDIT_DATE")
    return override or meta["audit_date"]


def catalog_year(meta: dict) -> int:
    return int(meta["catalog_year"])


def material_fingerprint(db_path: Path, meta: dict) -> str:
    conn = _connect(db_path)
    codes = [r["course_code"] for r in conn.execute("SELECT course_code FROM courses ORDER BY course_code")]
    codes.sort()
    payload = "|".join(codes) + "|" + meta["catalog_seed"]
    return hashlib.sha256(payload.encode()).hexdigest()


def run_stamp(scenario: str, digest: str) -> str:
    return hashlib.sha256(f"{digest}|{scenario}".encode()).hexdigest()[:16]


def map_transfer(source: str, year: int, rows: list[sqlite3.Row]) -> str:
    for row in rows:
        if row["source_code"] != source:
            continue
        if year < row["valid_from_year"] or year > row["valid_to_year"]:
            continue
        return row["target_code"]
    return source


def active_subs(audit_term: str, rows: list[sqlite3.Row]) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in rows:
        if audit_term <= row["expires_after_term"]:
            out[row["replaces_req_id"]] = row["sub_req_id"]
    return out


def fold_enrollments(enrolls: list[sqlite3.Row], courses: dict[str, sqlite3.Row]) -> dict[str, float]:
    best: dict[str, float] = {}
    credits: dict[str, float] = {}
    for e in enrolls:
        code = e["course_code"]
        gp = float(e["grade_points"])
        if code not in best or gp > best[code]:
            best[code] = gp
            credits[code] = float(courses[code]["credits"])
    return credits


def evaluate_requirements(conn, student_id: str, folded: dict[str, float], audit_term: str) -> list[dict]:
    reqs = conn.execute("SELECT * FROM requirements ORDER BY req_id").fetchall()
    req_courses = conn.execute("SELECT * FROM requirement_courses").fetchall()
    subs = active_subs(audit_term, conn.execute("SELECT * FROM substitutions").fetchall())
    waived = {r["req_id"] for r in conn.execute("SELECT req_id FROM waivers WHERE student_id = ?", (student_id,))}
    direct: dict[str, float] = {}
    for rc in req_courses:
        effective = rc["req_id"]
        if effective in subs:
            effective = subs[effective]
        if rc["course_code"] in folded:
            direct[effective] = direct.get(effective, 0.0) + folded[rc["course_code"]]
    children: dict[str, list[str]] = {}
    for r in reqs:
        if r["parent_req_id"]:
            children.setdefault(r["parent_req_id"], []).append(r["req_id"])
    status: dict[str, dict] = {}
    for r in reqs:
        sat = direct.get(r["req_id"], 0.0)
        if r["req_id"] in waived:
            sat = float(r["required_credits"])
        status[r["req_id"]] = {
            "req_id": r["req_id"],
            "satisfied_credits": sat,
            "required_credits": float(r["required_credits"]),
            "satisfied": sat >= float(r["required_credits"]),
        }
    for r in reqs:
        if not r["parent_req_id"]:
            stack = [r["req_id"]]
            while stack:
                parent = stack.pop()
                for child in children.get(parent, []):
                    child_st = status[child]
                    if child_st["satisfied"]:
                        p = status[parent]
                        p["satisfied_credits"] += child_st["satisfied_credits"]
                        p["satisfied"] = p["satisfied_credits"] >= p["required_credits"]
                        status[parent] = p
                    stack.append(child)
    return [status[r["req_id"]] for r in reqs]


def reference_report(fixture_root: Path, scenario: str) -> dict:
    db_path = fixture_root / "scenarios" / scenario / "degree.db"
    meta_path = fixture_root / "scenarios" / scenario / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    cy = catalog_year(meta)
    audit_term = meta["audit_term"]
    conn = _connect(db_path)
    courses = {r["course_code"]: r for r in conn.execute("SELECT * FROM courses")}
    allowed = {code: row for code, row in courses.items() if int(row["catalog_year"]) <= cy}
    equivs = conn.execute("SELECT * FROM transfer_equiv").fetchall()
    students = [r["student_id"] for r in conn.execute("SELECT student_id FROM students ORDER BY student_id")]
    digest = material_fingerprint(db_path, meta)
    student_rows = []
    for sid in students:
        enrolls = conn.execute(
            "SELECT * FROM enrollments WHERE student_id = ? ORDER BY course_code, term", (sid,)
        ).fetchall()
        mapped = []
        for e in enrolls:
            code = e["course_code"]
            if e["is_transfer"]:
                code = map_transfer(code, cy, equivs)
            if code not in allowed:
                continue
            row = dict(e)
            row["course_code"] = code
            mapped.append(row)
        folded = fold_enrollments(mapped, allowed)
        reqs = evaluate_requirements(conn, sid, folded, audit_term)
        reqs.sort(key=lambda r: r["req_id"])
        student_rows.append({"student_id": sid, "requirements": reqs})
    return {
        "scenario": scenario,
        "engine": "degaudit",
        "run_stamp": run_stamp(scenario, digest),
        "students": student_rows,
    }


def reference_material(fixture_root: Path, scenario: str) -> dict:
    db_path = fixture_root / "scenarios" / scenario / "degree.db"
    meta = json.loads((fixture_root / "scenarios" / scenario / "meta.json").read_text(encoding="utf-8"))
    conn = _connect(db_path)
    course_count = conn.execute("SELECT COUNT(*) AS c FROM courses").fetchone()["c"]
    enroll_count = conn.execute("SELECT COUNT(*) AS c FROM enrollments").fetchone()["c"]
    digest = material_fingerprint(db_path, meta)
    return {
        "scenario": scenario,
        "engine": "degaudit",
        "material_fingerprint": digest,
        "course_count": course_count,
        "enrollment_count": enroll_count,
    }
