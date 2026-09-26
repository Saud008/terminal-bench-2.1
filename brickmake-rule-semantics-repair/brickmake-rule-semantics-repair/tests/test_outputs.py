"""Builds brickmake from /app and replays makefile scenarios, comparing every
command's stdout, stderr, exit status and the resulting files with the output
GNU make 4.3 (-r -R) produced for the same scenario."""

import json
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(__file__))
from harness import play  # noqa: E402

BINARY = "/tmp/brickmake-verify"
with open(os.path.join(os.path.dirname(__file__), "cases.json"), encoding="utf-8") as fh:
    CASES = json.load(fh)


@pytest.fixture(scope="session")
def brickmake():
    if os.path.exists(BINARY):
        os.remove(BINARY)
    r = subprocess.run(
        ["/usr/local/go/bin/go", "build", "-o", BINARY, "./cmd/brickmake"],
        cwd="/app",
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert r.returncode == 0, f"go build failed:\n{r.stdout}{r.stderr}"
    return BINARY


def replay(binary, group):
    names = [n for n, c in CASES.items() if c["group"] == group]
    assert names, f"no scenarios for {group}"
    failures = []
    for name in names:
        case = CASES[name]
        got = play(case["steps"], [binary])
        for i, (g, want) in enumerate(zip(got, case["expect"])):
            if g != want:
                failures.append(f"{name} result #{i}\n  expected: {want!r}\n  actual:   {g!r}")
        if len(got) != len(case["expect"]):
            failures.append(f"{name}: expected {len(case['expect'])} results, got {len(got)}")
    assert not failures, "\n".join(failures)


def test_shortest_stem_selection(brickmake):
    """Among matching pattern rules the one with the shortest stem wins, where the
    stem of a directory-relative match includes the directory; ties keep makefile order."""
    replay(brickmake, "stem")


def test_directory_relative_prerequisites(brickmake):
    """For a slash-less target pattern matched against a name with a directory, the
    directory is prepended only to prerequisites that contain '%'."""
    replay(brickmake, "dirs")


def test_mentioned_prerequisite_ought_to_exist(brickmake):
    """A prerequisite that is mentioned anywhere in the makefile counts as one that
    ought to exist during the first implicit-rule pass, even without a rule of its own."""
    replay(brickmake, "mention")


def test_timestamps_reread_after_recipe(brickmake):
    """After a recipe runs the target's time is read again, so a recipe that leaves its
    target unchanged does not make dependents out of date; -n treats remade targets as new."""
    replay(brickmake, "restat")


def test_per_goal_messages(brickmake):
    """'Nothing to be done' and 'is up to date' are reported per goal, based only on
    whether that goal ran any command, including with -k."""
    replay(brickmake, "goals")


def test_pattern_specific_variable_order(brickmake):
    """Pattern-specific variables from all matching patterns apply from the shortest
    pattern to the longest, equal lengths in definition order; command-line values win."""
    replay(brickmake, "patvars")


def test_target_variable_inheritance(brickmake):
    """A target's own pattern-specific variables take precedence over the variables it
    inherits from the target that first asked for it."""
    replay(brickmake, "inherit")


def test_append_semantics(brickmake):
    """'+=' on a simply expanded variable expands the added text immediately and keeps
    it simple; a target-specific '+=' after its own definition extends that value."""
    replay(brickmake, "append")


def test_prerequisite_merge_order(brickmake):
    """A target's prerequisites from several rules are combined with the rule that has
    the recipe first, then the other rules in makefile order ($<, $^, $?, $| and build order)."""
    replay(brickmake, "merge")


def test_project_builds(brickmake):
    """Multi-step incremental builds of small projects produce the same commands,
    messages and files as GNU make across edits and rebuilds."""
    replay(brickmake, "project")
