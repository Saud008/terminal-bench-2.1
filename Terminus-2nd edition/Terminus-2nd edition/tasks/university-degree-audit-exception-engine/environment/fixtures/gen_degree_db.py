#!/usr/bin/env python3
"""Build SQLite degree audit scenarios with seeded randomized ids."""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_OUT = ROOT
HIDDEN_ROOT = Path(os.environ.get("DEGAUDIT_HIDDEN_ROOT", "")) if os.environ.get("DEGAUDIT_HIDDEN_ROOT") else None


def seed_ids(seed: str, labels: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for label in labels:
        digest = hashlib.sha256(f"{seed}:{label}".encode()).hexdigest()
        out[label] = f"{label[:3]}-{digest[:8]}"
    return out


def write_db(path: Path, meta: dict, rows: dict) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    conn = sqlite3.connect(str(path))
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE scenario_meta (scenario TEXT, audit_date TEXT, catalog_year INTEGER, audit_term TEXT, catalog_seed TEXT);
        CREATE TABLE students (student_id TEXT, display_name TEXT);
        CREATE TABLE courses (course_code TEXT, title TEXT, credits REAL, catalog_year INTEGER);
        CREATE TABLE enrollments (student_id TEXT, course_code TEXT, term TEXT, grade_points REAL, is_transfer INTEGER);
        CREATE TABLE transfer_equiv (source_code TEXT, target_code TEXT, valid_from_year INTEGER, valid_to_year INTEGER);
        CREATE TABLE substitutions (sub_req_id TEXT, replaces_req_id TEXT, expires_after_term TEXT);
        CREATE TABLE requirements (req_id TEXT, parent_req_id TEXT, required_credits REAL);
        CREATE TABLE requirement_courses (req_id TEXT, course_code TEXT);
        CREATE TABLE waivers (student_id TEXT, req_id TEXT, reason TEXT);
        """
    )
    cur.execute(
        "INSERT INTO scenario_meta VALUES (?,?,?,?,?)",
        (meta["scenario"], meta["audit_date"], meta["catalog_year"], meta["audit_term"], meta["catalog_seed"]),
    )
    for s in rows["students"]:
        cur.execute("INSERT INTO students VALUES (?,?)", (s["student_id"], s["display_name"]))
    for c in rows["courses"]:
        cur.execute(
            "INSERT INTO courses VALUES (?,?,?,?)",
            (c["course_code"], c["title"], c["credits"], c["catalog_year"]),
        )
    for e in rows["enrollments"]:
        cur.execute(
            "INSERT INTO enrollments VALUES (?,?,?,?,?)",
            (e["student_id"], e["course_code"], e["term"], e["grade_points"], 1 if e.get("is_transfer") else 0),
        )
    for t in rows.get("transfer_equiv", []):
        cur.execute(
            "INSERT INTO transfer_equiv VALUES (?,?,?,?)",
            (t["source_code"], t["target_code"], t["valid_from_year"], t["valid_to_year"]),
        )
    for sub in rows.get("substitutions", []):
        cur.execute(
            "INSERT INTO substitutions VALUES (?,?,?)",
            (sub["sub_req_id"], sub["replaces_req_id"], sub["expires_after_term"]),
        )
    for r in rows["requirements"]:
        cur.execute(
            "INSERT INTO requirements VALUES (?,?,?)",
            (r["req_id"], r.get("parent_req_id", ""), r["required_credits"]),
        )
    for rc in rows["requirement_courses"]:
        cur.execute(
            "INSERT INTO requirement_courses VALUES (?,?)",
            (rc["req_id"], rc["course_code"]),
        )
    for w in rows.get("waivers", []):
        cur.execute("INSERT INTO waivers VALUES (?,?,?)", (w["student_id"], w["req_id"], w["reason"]))
    conn.commit()
    conn.close()


def base_rows(seed: str) -> dict:
    ids = seed_ids(
        seed,
        ["stu-1", "c-math", "c-eng", "req-core", "req-math", "req-eng"],
    )
    return {
        "students": [{"student_id": ids["stu-1"], "display_name": "Alex Student"}],
        "courses": [
            {"course_code": ids["c-math"], "title": "Calculus", "credits": 3.0, "catalog_year": 2024},
            {"course_code": ids["c-eng"], "title": "Composition", "credits": 3.0, "catalog_year": 2024},
        ],
        "requirements": [
            {"req_id": ids["req-core"], "parent_req_id": "", "required_credits": 6.0},
            {"req_id": ids["req-math"], "parent_req_id": ids["req-core"], "required_credits": 3.0},
            {"req_id": ids["req-eng"], "parent_req_id": ids["req-core"], "required_credits": 3.0},
        ],
        "requirement_courses": [
            {"req_id": ids["req-math"], "course_code": ids["c-math"]},
            {"req_id": ids["req-eng"], "course_code": ids["c-eng"]},
        ],
        "enrollments": [
            {
                "student_id": ids["stu-1"],
                "course_code": ids["c-math"],
                "term": "2024-Fall",
                "grade_points": 3.5,
            },
            {
                "student_id": ids["stu-1"],
                "course_code": ids["c-eng"],
                "term": "2024-Fall",
                "grade_points": 3.0,
            },
        ],
        "transfer_equiv": [],
        "substitutions": [],
        "waivers": [],
    }


def scenario_clean_audit(seed: str) -> dict:
    return base_rows(seed)


def scenario_transfer_equiv(seed: str) -> dict:
    rows = base_rows(seed)
    ids = seed_ids(seed, ["c-xfer", "c-local"])
    rows["courses"].append(
        {"course_code": ids["c-local"], "title": "Local Stats", "credits": 3.0, "catalog_year": 2024}
    )
    rows["requirement_courses"].append({"req_id": rows["requirements"][1]["req_id"], "course_code": ids["c-local"]})
    rows["transfer_equiv"] = [
        {
            "source_code": ids["c-xfer"],
            "target_code": ids["c-local"],
            "valid_from_year": 2023,
            "valid_to_year": 2025,
        }
    ]
    rows["enrollments"] = [
        {
            "student_id": rows["students"][0]["student_id"],
            "course_code": ids["c-xfer"],
            "term": "2023-Fall",
            "grade_points": 3.7,
            "is_transfer": True,
        }
    ]
    return rows


def scenario_substitution_active(seed: str) -> dict:
    rows = base_rows(seed)
    ids = seed_ids(seed, ["c-alt", "req-alt"])
    rows["courses"].append({"course_code": ids["c-alt"], "title": "Alt Math", "credits": 3.0, "catalog_year": 2024})
    rows["requirements"].append({"req_id": ids["req-alt"], "parent_req_id": "", "required_credits": 3.0})
    rows["requirement_courses"].append({"req_id": ids["req-alt"], "course_code": ids["c-alt"]})
    math_req = rows["requirements"][1]["req_id"]
    rows["substitutions"] = [
        {"sub_req_id": ids["req-alt"], "replaces_req_id": math_req, "expires_after_term": "2026-Spring"}
    ]
    rows["enrollments"] = [
        {
            "student_id": rows["students"][0]["student_id"],
            "course_code": ids["c-alt"],
            "term": "2024-Fall",
            "grade_points": 3.2,
        }
    ]
    return rows


def scenario_catalog_year_lock(seed: str) -> dict:
    rows = base_rows(seed)
    ids = seed_ids(seed, ["c-old"])
    rows["courses"].append({"course_code": ids["c-old"], "title": "Legacy Seminar", "credits": 3.0, "catalog_year": 2022})
    rows["requirement_courses"].append({"req_id": rows["requirements"][2]["req_id"], "course_code": ids["c-old"]})
    rows["enrollments"].append(
        {
            "student_id": rows["students"][0]["student_id"],
            "course_code": ids["c-old"],
            "term": "2024-Fall",
            "grade_points": 3.0,
        }
    )
    rows["meta_catalog_year"] = 2023
    return rows


def scenario_repeat_retake(seed: str) -> dict:
    rows = base_rows(seed)
    math = rows["courses"][0]["course_code"]
    sid = rows["students"][0]["student_id"]
    rows["enrollments"] = [
        {"student_id": sid, "course_code": math, "term": "2023-Fall", "grade_points": 2.0},
        {"student_id": sid, "course_code": math, "term": "2024-Spring", "grade_points": 3.8},
    ]
    return rows


def scenario_requirement_closure(seed: str) -> dict:
    return scenario_clean_audit(seed)


def scenario_exception_waiver(seed: str) -> dict:
    rows = base_rows(seed)
    eng_req = rows["requirements"][2]["req_id"]
    rows["enrollments"] = [rows["enrollments"][0]]
    rows["waivers"] = [
        {"student_id": rows["students"][0]["student_id"], "req_id": eng_req, "reason": "study-abroad"}
    ]
    return rows


def scenario_stable_report(seed: str) -> dict:
    return scenario_clean_audit(seed)


def scenario_catalog_year_trap(seed: str) -> dict:
    rows = scenario_catalog_year_lock(seed)
    rows["meta_catalog_year"] = 2024
    rows["courses"][-1]["catalog_year"] = 2024
    return rows


def scenario_subst_expiry_trap(seed: str) -> dict:
    rows = scenario_substitution_active(seed)
    rows["meta_audit_term"] = rows["substitutions"][0]["expires_after_term"]
    return rows


BUILDERS = {
    "clean-audit": scenario_clean_audit,
    "transfer-equiv": scenario_transfer_equiv,
    "substitution-active": scenario_substitution_active,
    "catalog-year-lock": scenario_catalog_year_lock,
    "repeat-retake": scenario_repeat_retake,
    "requirement-closure": scenario_requirement_closure,
    "exception-waiver": scenario_exception_waiver,
    "stable-report": scenario_stable_report,
    "catalog-year-trap": scenario_catalog_year_trap,
    "subst-expiry-trap": scenario_subst_expiry_trap,
}


def emit(name: str, out_root: Path) -> None:
    seed = hashlib.sha256(name.encode()).hexdigest()[:16]
    builder = BUILDERS[name]
    rows = builder(seed)
    catalog_year = rows.pop("meta_catalog_year", 2024)
    audit_term = rows.pop("meta_audit_term", "2025-Fall")
    meta = {
        "scenario": name,
        "audit_date": rows.pop("meta_audit_date", "2025-10-01"),
        "catalog_year": catalog_year,
        "audit_term": audit_term,
        "catalog_seed": seed,
    }
    dest = out_root / "scenarios" / name
    write_db(dest / "degree.db", meta, rows)
    (dest / "meta.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")


BUNDLED = (
    "clean-audit",
    "transfer-equiv",
    "substitution-active",
    "catalog-year-lock",
    "repeat-retake",
    "requirement-closure",
    "exception-waiver",
    "stable-report",
)
HIDDEN = (
    "catalog-year-trap",
    "subst-expiry-trap",
)


def main() -> None:
    targets = [DEFAULT_OUT]
    if HIDDEN_ROOT is not None and HIDDEN_ROOT.is_dir():
        targets.append(HIDDEN_ROOT)
    for out_root in targets:
        names = list(BUNDLED) if out_root == DEFAULT_OUT else list(HIDDEN)
        for name in names:
            emit(name, out_root)


if __name__ == "__main__":
    main()
