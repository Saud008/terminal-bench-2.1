"""Behavioral checks for shiftclock against glibc-derived answers on held-out TZif files."""

import json
import os
import subprocess
import time
from pathlib import Path

import pytest

APP = Path("/app")
TESTS = Path(__file__).resolve().parent
ZONES = TESTS / "zones"
EXPECTED = json.loads((TESTS / "expected.json").read_text(encoding="utf-8"))
BINARY = "/tmp/shiftclock-verify"


@pytest.fixture(scope="session")
def shiftclock():
    env = dict(os.environ, GOTOOLCHAIN="local", GOPROXY="off", CGO_ENABLED="0")
    result = subprocess.run(
        ["/usr/local/go/bin/go", "build", "-o", BINARY, "./cmd/shiftclock"],
        cwd=APP,
        env=env,
        capture_output=True,
        text=True,
        timeout=900,
    )
    assert result.returncode == 0, f"go build ./cmd/shiftclock failed:\n{result.stderr}"
    return BINARY


def run(binary, args, env=None):
    result = subprocess.run(
        [binary, *args],
        capture_output=True,
        text=True,
        timeout=120,
        env=dict(os.environ, **(env or {})),
    )
    assert result.returncode == 0, f"shiftclock {' '.join(args[:3])} exited {result.returncode}: {result.stderr}"
    return result.stdout.splitlines()


def utc(t):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def wanted(row):
    t, local, offset, abbr, isdst = row
    return {"utc": utc(t), "local": local, "offset": offset, "abbr": abbr, "isdst": isdst}


def wrong_answers(binary, zone, zone_arg=None, env=None, iso=False):
    rows = EXPECTED["at"][zone]
    instants = [utc(r[0]) if iso else str(r[0]) for r in rows]
    lines = run(binary, ["at", "--zone", zone_arg or str(ZONES / zone), "--", *instants], env)
    assert len(lines) == len(rows), f"{zone}: {len(lines)} output lines for {len(rows)} instants"
    bad = []
    for row, line in zip(rows, lines):
        got, want = json.loads(line), wanted(row)
        if got != want:
            bad.append(f"{zone} at {want['utc']}: got {got}, want {want}")
    return bad


def assert_zones(binary, zones):
    bad = [msg for zone in zones for msg in wrong_answers(binary, zone)]
    assert not bad, f"{len(bad)} wrong answers; first ones:\n" + "\n".join(bad[:8])


def test_us_rules_after_table_end(shiftclock):
    """Zones whose tables stop in 2007/2012 follow their M3.2.0/M11.1.0 footers, including both changes each year."""
    assert_zones(shiftclock, ["America/Chicago", "America/Havana"])


def test_last_weekday_of_month_rules(shiftclock):
    """Mm.5.d selects the last such weekday of the month, including February in leap and common years."""
    assert_zones(shiftclock, ["Europe/Lisbon", "LastWeek/February", "LastWeek/Leapday"])


def test_daylight_time_spanning_new_year(shiftclock):
    """Southern-hemisphere, negative-save and two-hour-save footers resolve correctly on both sides of each change."""
    assert_zones(shiftclock, ["Pacific/Easter", "Australia/Lord_Howe", "Negative/Winter", "Antarctica/Troll"])


def test_signed_and_extended_rule_hours(shiftclock):
    """RFC 8536 rule times: negative hours, hours past 24 and up to 167, with minutes, in real and synthetic zones."""
    assert_zones(
        shiftclock,
        ["America/Scoresbysund", "Asia/Jerusalem", "Asia/Gaza", "Extended/Minus", "Extended/Week", "Extended/Southern"],
    )


def test_julian_and_zero_based_day_rules(shiftclock):
    """Jn ignores February 29 while zero-based n counts it, in both leap and common years."""
    assert_zones(shiftclock, ["Julian/Harbor", "ZeroBased/Harbor", "Julian/Austral", "ZeroBased/Austral"])


def test_transitions_listing(shiftclock):
    """transitions lists every change in the UTC year range, in order, across table/footer boundaries."""
    bad = []
    for zone, first, last, items in EXPECTED["transitions"]:
        lines = run(shiftclock, ["transitions", "--zone", str(ZONES / zone), "--from", str(first), "--to", str(last)])
        got = [json.loads(line) for line in lines]
        want = [{"at": at, "offset": off, "abbr": abbr, "isdst": dst} for at, off, abbr, dst in items]
        if got != want:
            bad.append(f"{zone} {first}-{last}:\n  got  {got}\n  want {want}")
    assert not bad, "\n".join(bad)


def test_zone_names_resolve_under_zoneinfo_dir(shiftclock):
    """A bare zone name is looked up under SHIFTCLOCK_ZONEINFO and RFC 3339 instants are accepted."""
    env = {"SHIFTCLOCK_ZONEINFO": str(ZONES)}
    bad = []
    for zone in ["America/Santiago", "Europe/Dublin"]:
        bad += wrong_answers(shiftclock, zone, zone_arg=zone, env=env, iso=True)
    assert not bad, f"{len(bad)} wrong answers; first ones:\n" + "\n".join(bad[:8])


def test_output_lines_use_documented_key_order(shiftclock):
    """Each at/transitions line is compact JSON with keys in the documented order and correct values."""
    zone = "Australia/Lord_Howe"
    row = next(r for r in EXPECTED["at"][zone] if r[0] > 2208988800 and r[4])
    t, local, offset, abbr, isdst = row
    line = run(shiftclock, ["at", "--zone", str(ZONES / zone), str(t)])
    assert line == [
        f'{{"utc":"{utc(t)}","local":"{local}","offset":{offset},"abbr":"{abbr}","isdst":{json.dumps(isdst)}}}'
    ]

    zone, first, last, items = next(e for e in EXPECTED["transitions"] if e[0] == "Antarctica/Troll")
    lines = run(shiftclock, ["transitions", "--zone", str(ZONES / zone), "--from", str(first), "--to", str(last)])
    assert lines == [
        f'{{"at":"{at}","offset":{off},"abbr":"{abbr}","isdst":{json.dumps(dst)}}}' for at, off, abbr, dst in items
    ]


def leap_wanted(reading, local, offset, abbr, isdst):
    return {"utc": reading, "local": local, "offset": offset, "abbr": abbr, "isdst": isdst}


def test_leap_second_files_read_through_their_records(shiftclock):
    """In files with leap-second records, Unix-second instants count leap seconds: utc/local are corrected readings and
    an inserted leap second reads as second 60 (real right/ zones, a version-1-only file, a negative leap second)."""
    bad = []
    for zone, rows in EXPECTED["leap_at"].items():
        lines = run(shiftclock, ["at", "--zone", str(ZONES / zone), "--", *[str(r[0]) for r in rows]])
        assert len(lines) == len(rows), f"{zone}: {len(lines)} output lines for {len(rows)} instants"
        for (t, *fields), line in zip(rows, lines):
            got, want = json.loads(line), leap_wanted(*fields)
            if got != want:
                bad.append(f"{zone} at {t}: got {got}, want {want}")
    assert not bad, f"{len(bad)} wrong answers; first ones:\n" + "\n".join(bad[:8])


def test_leap_second_rfc3339_instants(shiftclock):
    """RFC 3339 instants in leap-second files are UTC readings mapped through the records, including second 60."""
    bad = []
    for zone in dict.fromkeys(case[0] for case in EXPECTED["leap_iso"]):
        cases = [case[1:] for case in EXPECTED["leap_iso"] if case[0] == zone]
        lines = run(shiftclock, ["at", "--zone", str(ZONES / zone), *[iso for iso, *_ in cases]])
        assert len(lines) == len(cases), f"{zone}: {len(lines)} output lines for {len(cases)} instants"
        for (iso, *fields), line in zip(cases, lines):
            got, want = json.loads(line), leap_wanted(*fields)
            if got != want:
                bad.append(f"{zone} at {iso}: got {got}, want {want}")
    assert not bad, f"{len(bad)} wrong answers; first ones:\n" + "\n".join(bad[:8])


def test_leap_second_transitions_and_year_bounds(shiftclock):
    """transitions in leap-second files reports UTC readings and bounds the years by UTC reading, not raw seconds."""
    bad = []
    for zone, first, last, items in EXPECTED["leap_transitions"]:
        lines = run(shiftclock, ["transitions", "--zone", str(ZONES / zone), "--from", str(first), "--to", str(last)])
        got = [json.loads(line) for line in lines]
        want = [{"at": at, "offset": off, "abbr": abbr, "isdst": dst} for at, off, abbr, dst in items]
        if got != want:
            bad.append(f"{zone} {first}-{last}:\n  got  {got}\n  want {want}")
    assert not bad, "\n".join(bad)
