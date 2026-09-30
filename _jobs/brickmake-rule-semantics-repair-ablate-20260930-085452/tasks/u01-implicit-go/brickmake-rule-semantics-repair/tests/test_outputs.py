"""Builds brickmake from /app and replays makefile scenarios, comparing every
command's stdout, stderr, exit status and the resulting files with the output
GNU make 4.3 (-r -R) produced for the same scenario."""

import functools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from harness import build, play  # noqa: E402

with open(os.path.join(os.path.dirname(__file__), "cases.json"), encoding="utf-8") as fh:
    CASES = json.load(fh)


@functools.lru_cache(maxsize=1)
def brickmake():
    return build()


def replay(group):
    binary = brickmake()
    names = [n for n, c in CASES.items() if c["group"] == group]
    assert names, f"no scenarios for {group}"
    failures = []
    for name in names:
        case = CASES[name]
        got = play(case["steps"], binary)
        for i, (g, want) in enumerate(zip(got, case["expect"])):
            if g != want:
                failures.append(f"{name} result #{i}\n  expected: {want!r}\n  actual:   {g!r}")
        if len(got) != len(case["expect"]):
            failures.append(f"{name}: expected {len(case['expect'])} results, got {len(got)}")
    assert not failures, "\n".join(failures)


def test_cli_builds_and_rebuilds():
    """/app/cmd/brickmake compiles with the standard library only, runs a default-goal
    build whose recipes create the objects on disk, and rebuilds only what was removed."""
    replay("smoke")


def test_shortest_stem_selection():
    """Among matching pattern rules the one with the shortest stem wins, where the
    stem of a directory-relative match includes the directory; ties keep makefile order."""
    replay("stem")


def test_directory_relative_prerequisites():
    """For a slash-less target pattern matched against a name with a directory, the
    directory is prepended only to prerequisites that contain '%'."""
    replay("dirs")


def test_mentioned_prerequisite_ought_to_exist():
    """A prerequisite that is mentioned anywhere in the makefile counts as one that
    ought to exist during the first implicit-rule pass, even without a rule of its own."""
    replay("mention")


def test_pattern_specific_variable_order():
    """Pattern-specific variables from all matching patterns apply from the shortest
    pattern to the longest, equal lengths in definition order; command-line values win."""
    replay("patvars")


def test_project_builds():
    """Multi-step incremental builds of small projects produce the same commands,
    messages and files left on disk as GNU make across edits and rebuilds."""
    replay("project")
