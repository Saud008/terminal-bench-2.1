"""Independent verifier math for offline MQTT session journal curation."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, "/app/fixtures")
from digest_util import sha256_canonical_json


def session_expiry_ms() -> int | None:
    raw = os.environ.get("TB3_SESSION_EXPIRY_MS", "")
    if raw:
        return int(raw)
    return None


def mqtt_match(filter_topic: str, topic: str) -> bool:
    f_parts = filter_topic.split("/")
    t_parts = topic.split("/")
    fi = ti = 0
    while fi < len(f_parts):
        if f_parts[fi] == "#":
            return fi == len(f_parts) - 1
        if ti >= len(t_parts):
            return False
        if f_parts[fi] == "+":
            if t_parts[ti] == "":
                return False
            fi += 1
            ti += 1
            continue
        if f_parts[fi] != t_parts[ti]:
            return False
        fi += 1
        ti += 1
    return ti == len(t_parts)


def read_journal(fixture_root: Path, scenario: str) -> list[dict[str, Any]]:
    path = fixture_root / "broker-journals" / scenario / "events.jsonl"
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            events.append(json.loads(line))
    return sorted(events, key=lambda e: e["seq"])


def canonical_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for ev in events:
        row = {
            "seq": ev["seq"],
            "kind": ev["kind"],
            "client_id": ev.get("client_id", ""),
            "topic": ev.get("topic", ""),
            "filter": ev.get("filter", ""),
            "payload": ev.get("payload", ""),
            "qos": ev.get("qos", 0),
            "retain": ev.get("retain", False),
            "packet_id": ev.get("packet_id", 0),
            "timestamp_ms": ev["timestamp_ms"],
            "clean_session": ev.get("clean_session", False),
            "session_expiry_ms": ev.get("session_expiry_ms", 0),
        }
        out.append(row)
    return out


def reference_staging(broker: str, scenario: str, fixture_root: Path) -> dict[str, Any]:
    events = read_journal(fixture_root, scenario)
    canonical = canonical_events(events)
    payload = {"broker": broker, "scenario": scenario, "events": canonical}
    digest = sha256_canonical_json(payload)
    return {
        "engine": "mqttsessctl",
        "broker": broker,
        "scenario": scenario,
        "event_count": len(events),
        "events": events,
        "staging_digest": digest,
    }


def _apply_retained(store: dict[str, dict[str, Any]], ev: dict[str, Any]) -> None:
    if not ev.get("retain"):
        return
    topic = ev["topic"]
    if ev.get("payload", "") == "":
        store.pop(topic, None)
        return
    cur = store.get(topic)
    if cur is None or ev["timestamp_ms"] >= cur["timestamp_ms"]:
        store[topic] = {"payload": ev["payload"], "timestamp_ms": ev["timestamp_ms"]}


def _event_allowed(sessions: dict[str, dict[str, Any]], client: str, ts: int) -> bool:
    sess = sessions.get(client)
    if not sess or not sess.get("active", True):
        return False
    expiry = session_expiry_ms()
    window = expiry if expiry is not None else sess.get("session_expiry_ms", 0)
    if window and ts > sess["connect_ms"] + window:
        return False
    return True


def reference_export(broker: str, scenario: str, fixture_root: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    events = read_journal(fixture_root, scenario)
    sessions: dict[str, dict[str, Any]] = {}
    subs: dict[str, list[str]] = {}
    retain: dict[str, dict[str, Any]] = {}
    qos1: dict[str, set[int]] = {}
    qos2: dict[str, set[int]] = {}
    ledger: list[dict[str, Any]] = []
    seq = 0

    for ev in events:
        kind = ev["kind"]
        client = ev.get("client_id", "")
        ts = ev["timestamp_ms"]
        if kind == "CONNECT":
            if ev.get("clean_session"):
                sessions.pop(client, None)
                subs.pop(client, None)
            sessions[client] = {
                "connect_ms": ts,
                "session_expiry_ms": ev.get("session_expiry_ms", 0),
                "active": True,
            }
        elif kind == "SUBSCRIBE":
            if not _event_allowed(sessions, client, ts):
                continue
            subs.setdefault(client, []).append(ev["filter"])
        elif kind == "PUBLISH":
            _apply_retained(retain, ev)
            for sub_client, filters in subs.items():
                if not _event_allowed(sessions, sub_client, ts):
                    continue
                for filt in filters:
                    if mqtt_match(filt, ev["topic"]):
                        qos = ev.get("qos", 0)
                        pid = ev.get("packet_id", 0)
                        deliver = True
                        if qos == 1:
                            seen = qos1.setdefault(sub_client, set())
                            if pid in seen:
                                deliver = False
                            else:
                                seen.add(pid)
                        elif qos == 2:
                            seen = qos2.setdefault(sub_client, set())
                            if pid in seen:
                                deliver = False
                            else:
                                seen.add(pid)
                        if deliver:
                            seq += 1
                            ledger.append(
                                {
                                    "client_id": sub_client,
                                    "topic": ev["topic"],
                                    "payload": ev["payload"],
                                    "qos": qos,
                                    "packet_id": pid,
                                    "delivery_seq": seq,
                                    "offline": True,
                                }
                            )
        elif kind == "PUBACK":
            qos1.setdefault(client, set()).discard(ev.get("packet_id", 0))
        elif kind == "PUBREC":
            pass
        elif kind == "PUBCOMP":
            qos2.setdefault(client, set()).discard(ev.get("packet_id", 0))

    retained_snap = {t: v["payload"] for t, v in retain.items()}
    atlas: list[dict[str, Any]] = []
    for client, filters in subs.items():
        for filt in filters:
            for topic, payload in retained_snap.items():
                atlas.append(
                    {
                        "client_id": client,
                        "filter": filt,
                        "topic": topic,
                        "matched": mqtt_match(filt, topic),
                        "retained_payload": payload if mqtt_match(filt, topic) else "",
                        "qos": 0,
                    }
                )
    atlas.sort(key=lambda r: (r["client_id"], r["filter"], r["topic"]))
    ledger.sort(key=lambda r: r["delivery_seq"])
    return atlas, ledger


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows
