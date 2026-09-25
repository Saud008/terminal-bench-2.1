"""Independent polkit-style decision reference (anti-cheat)."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RuleBlock:
    action_id: str
    user: str
    local: str
    active: str
    result: str
    source_file: str


def rules_root(app: Path, tb3: str | None = None) -> Path:
    if tb3:
        return Path(tb3) / "rules"
    return app / "fixtures" / "rules"


def actions_root(app: Path, tb3: str | None = None) -> Path:
    if tb3:
        return Path(tb3) / "actions"
    return app / "fixtures" / "actions"


def parse_prefix(filename: str) -> tuple[int, str]:
    m = re.match(r"^(\d+)-(.+)\.rules$", filename)
    if not m:
        return 999999, filename
    return int(m.group(1)), m.group(2)


def parse_rule_file(path: Path) -> list[RuleBlock]:
    blocks: list[RuleBlock] = []
    cur: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "block":
            cur = {}
            continue
        if line == "end":
            if cur:
                blocks.append(
                    RuleBlock(
                        action_id=cur["action_id"],
                        user=cur.get("user", "*"),
                        local=cur.get("local", "any"),
                        active=cur.get("active", "any"),
                        result=cur["result"],
                        source_file=path.name,
                    )
                )
            cur = {}
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            cur[k.strip()] = v.strip()
    return blocks


def merge_rules(app: Path, stack: str, tb3: str | None = None) -> list[RuleBlock]:
    root = rules_root(app, tb3) / stack
    files = sorted(root.glob("*.rules"), key=lambda p: (parse_prefix(p.name), p.name))
    merged: list[RuleBlock] = []
    for path in files:
        for block in parse_rule_file(path):
            merged.append(block)
    return merged


def subject_match(block: RuleBlock, subject: dict[str, Any]) -> bool:
    user = subject["user"]
    if block.user != "*" and block.user != user:
        return False
    local = subject["local"]
    active = subject["active"]
    if block.local != "any" and (block.local == "true") != bool(local):
        return False
    if block.active != "any" and (block.active == "true") != bool(active):
        return False
    return True


def pick_rule(blocks: list[RuleBlock], action_id: str, subject: dict[str, Any]) -> RuleBlock | None:
    match: RuleBlock | None = None
    for block in blocks:
        if block.action_id == action_id and subject_match(block, subject):
            match = block
    return match


def load_action_js(path: Path) -> dict[str, str] | None:
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        "allow_active": data["allow_active"],
        "allow_inactive": data["allow_inactive"],
    }


def load_action_xml(path: Path) -> dict[str, str] | None:
    if not path.is_file():
        return None
    root = ET.fromstring(path.read_text(encoding="utf-8"))
    return {
        "allow_active": root.findtext("allow_active", "no"),
        "allow_inactive": root.findtext("allow_inactive", "no"),
    }


def lookup_action(app: Path, action_id: str, tb3: str | None = None) -> tuple[str | None, str | None]:
    root = actions_root(app, tb3)
    js_path = root / f"{action_id}.js"
    xml_path = root / f"{action_id}.xml"
    js = load_action_js(js_path)
    if js:
        return "js", json.dumps(js)
    xml = load_action_xml(xml_path)
    if xml:
        return "xml", json.dumps(xml)
    return None, None


def map_subject_token(subject: dict[str, Any], allow_active: str, allow_inactive: str) -> str:
    active = bool(subject["active"])
    if active:
        return allow_active
    return allow_inactive


def apply_challenge(
    base: str,
    challenge: str | None,
    prior: dict[str, Any] | None,
    seat: str,
) -> tuple[str, str | None, bool]:
    """Return decision, echoed challenge, implicit flag."""
    if challenge is None:
        if base == "yes":
            return "allow", None, True
        if base == "no":
            return "deny", None, False
        return "challenge", base, False

    if challenge == "auth_self":
        if prior and prior.get("challenge") == "auth_admin_keep" and prior.get("seat") == seat:
            return "challenge", "auth_self", False
        if prior and prior.get("challenge") == "auth_admin" and prior.get("seat") == seat:
            if base in {"auth_self", "auth_admin"}:
                return "allow", None, False
        if base == "no":
            return "deny", None, False
        return "challenge", "auth_self", False

    if challenge in {"auth_admin", "auth_admin_keep"}:
        if base == "no":
            return "deny", None, False
        if prior and prior.get("seat") == seat:
            if prior.get("challenge") == challenge:
                return "allow", None, False
            if challenge == "auth_admin" and prior.get("challenge") == "auth_admin_keep":
                return "allow", None, False
        return "challenge", challenge, False

    return "challenge", challenge, False


def cache_key(action_id: str, user: str, seat: str) -> str:
    return f"{action_id}|{user}|{seat}"


def read_cache(app: Path) -> dict[str, bool]:
    path = app / "state" / "auth-cache.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_cache(app: Path, cache: dict[str, bool]) -> None:
    path = app / "state" / "auth-cache.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cache, sort_keys=True), encoding="utf-8")


def evaluate(app: Path, scenario: dict[str, Any], tb3: str | None = None) -> dict[str, Any]:
    action_id = scenario["action_id"]
    subject = scenario["subject"]
    stack = scenario["rules_stack"]
    challenge = scenario.get("challenge")
    prior = scenario.get("prior_grant")

    blocks = merge_rules(app, stack, tb3)
    rule = pick_rule(blocks, action_id, subject)

    source = "none"
    matched_rule: str | None = None
    token: str

    if rule:
        token = rule.result
        source = f"rule:{rule.source_file}"
        matched_rule = rule.source_file
    else:
        fmt, payload = lookup_action(app, action_id, tb3)
        if fmt is None:
            return {
                "decision": "deny",
                "source": "none",
                "challenge": None,
                "implicit": False,
                "matched_rule": None,
            }
        fields = json.loads(payload)
        token = map_subject_token(subject, fields["allow_active"], fields["allow_inactive"])
        source = f"action:{fmt}:{action_id}"

    decision, echoed, implicit = apply_challenge(token, challenge, prior, subject["seat"])

    if decision == "allow" and implicit:
        ck = cache_key(action_id, subject["user"], subject["seat"])
        cache = read_cache(app)
        if cache.get(ck):
            return {
                "decision": "cached_allow",
                "source": "cache",
                "challenge": None,
                "implicit": True,
                "matched_rule": None,
            }
        cache[ck] = True
        write_cache(app, cache)

    return {
        "decision": decision,
        "source": source,
        "challenge": echoed,
        "implicit": implicit and decision == "allow",
        "matched_rule": matched_rule,
    }
