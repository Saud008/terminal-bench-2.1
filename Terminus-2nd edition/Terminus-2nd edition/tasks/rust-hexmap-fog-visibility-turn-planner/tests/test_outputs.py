"""Independent fogpf playtest planner behavioral checks with Python reference math.

Verifiers assert fog-mask snapshot rows after ingest load-board and export seal-atlas.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

APP_ROOT = Path("/app")
CLI = APP_ROOT / "bin" / "fogpf"
RESET = APP_ROOT / "scripts" / "reset-playfield.sh"
BOARD_ROOT = APP_ROOT / "fixtures" / "boards"
ROSTER_DIR = APP_ROOT / "state" / "board-roster"
RAY_DIR = APP_ROOT / "work" / "los-rays"
MASK_DIR = APP_ROOT / "work" / "fog-mask"
OUT_DIR = APP_ROOT / "output"


def invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        cmd, cwd=str(APP_ROOT), capture_output=True, text=True, check=False, env=merged
    )


def wipe() -> None:
    proc = invoke(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def board_path(name: str, env: dict | None = None) -> Path:
    root = Path(env["TB3_BOARD_DIR"]) if env and env.get("TB3_BOARD_DIR") else BOARD_ROOT
    return root / f"{name}.json"


def cube_dist(q0: int, r0: int, q1: int, r1: int) -> int:
    s0 = -q0 - r0
    s1 = -q1 - r1
    return (abs(q1 - q0) + abs(r1 - r0) + abs(s1 - s0)) // 2


DIRS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]


def hex_line(q0: int, r0: int, q1: int, r1: int) -> list[tuple[int, int]]:
    out = [(q0, r0)]
    q, r = q0, r0
    guard = 0
    while (q, r) != (q1, r1):
        best = None
        best_d = 10**9
        for dq, dr in DIRS:
            nq, nr = q + dq, r + dr
            d = cube_dist(nq, nr, q1, r1)
            take = best is None or d < best_d or (d == best_d and (nq, nr) < best)
            if take:
                best_d = d
                best = (nq, nr)
        assert best is not None
        q, r = best
        out.append((q, r))
        guard += 1
        if guard > 256:
            break
    return out


def vision_radius(klass: str) -> int:
    return {"scout": 4, "infantry": 2, "tower": 3}.get(klass, 1)


def clear_los(obs, tgt, elev: dict[tuple[int, int], int]) -> bool:
    line = hex_line(obs[0], obs[1], tgt[0], tgt[1])
    if len(line) <= 2:
        return True
    floor = min(elev.get(obs, 0), elev.get(tgt, 0))
    for cell in line[1:-1]:
        if elev.get(cell, 0) > floor:
            return False
    return True


def expected_visible(board: dict) -> list[dict]:
    elev = {(c["q"], c["r"]): c["elev"] for c in board["cells"]}
    seen: set[tuple[int, int]] = set()
    for u in board["units"]:
        rad = vision_radius(u["class"])
        o = (u["q"], u["r"])
        for c in board["cells"]:
            t = (c["q"], c["r"])
            if cube_dist(o[0], o[1], t[0], t[1]) <= rad and clear_los(o, t, elev):
                seen.add(t)
    return [{"q": q, "r": r} for q, r in sorted(seen)]


def reference_visible(board: dict) -> list[dict]:
    return expected_visible(board)


def pipeline(run_id: str, board: Path, env: dict | None = None) -> dict:
    wipe()
    assert invoke([str(CLI), "load-board", "--run-id", run_id, "--board", str(board)], env).returncode == 0
    assert invoke([str(CLI), "place-units", "--run-id", run_id], env).returncode == 0
    assert invoke([str(CLI), "resolve-los", "--run-id", run_id], env).returncode == 0
    assert invoke([str(CLI), "reveal-fog", "--run-id", run_id], env).returncode == 0
    assert invoke([str(CLI), "seal-atlas", "--run-id", run_id], env).returncode == 0
    return json.loads((OUT_DIR / f"{run_id}-fog-atlas.json").read_text(encoding="utf-8"))


def test_t016c5d_plains_scout_atlas_visible_count_and_win():
    """Plains scout atlas visible_count and win_condition_met match cube-distance reference."""
    board = json.loads(board_path("plains-01").read_text(encoding="utf-8"))
    atlas = pipeline("plains-run", board_path("plains-01"))
    exp = expected_visible(board)
    assert atlas["board_id"] == "plains-01"
    assert atlas["visible_count"] == len(exp)
    assert atlas["visible_cells"] == exp
    assert atlas["win_condition_met"] == (len(exp) >= board["target_reveal"])


def test_t016c5d_ridge_elevation_blocks_far_cell():
    """Ridge elevation greater than min(obs,tgt) blocks LOS to the far cell."""
    board = json.loads(board_path("ridge-02").read_text(encoding="utf-8"))
    elev = {(c["q"], c["r"]): c["elev"] for c in board["cells"]}
    assert clear_los((0, 0), (2, 0), elev) is False
    atlas = pipeline("ridge-block", board_path("ridge-02"))
    cells = {(c["q"], c["r"]) for c in atlas["visible_cells"]}
    assert (2, 0) not in cells


def test_t016c5d_equal_elevation_peek_allowed():
    """Equal elevation along a ray does not block LOS peek."""
    board = json.loads(board_path("ridge-02").read_text(encoding="utf-8"))
    elev = {(c["q"], c["r"]): c["elev"] for c in board["cells"]}
    assert clear_los((0, 2), (2, 2), elev) is True
    atlas = pipeline("ridge-peek", board_path("ridge-02"))
    cells = {(c["q"], c["r"]) for c in atlas["visible_cells"]}
    assert (2, 2) in cells


def test_t016c5d_scout_vision_radius_four_on_plains():
    """Scout class uses vision radius 4 on plains playfield."""
    board = json.loads(board_path("plains-01").read_text(encoding="utf-8"))
    assert vision_radius("scout") == 4
    atlas = pipeline("scout-rad", board_path("plains-01"))
    for c in atlas["visible_cells"]:
        assert cube_dist(0, 0, c["q"], c["r"]) <= 4
    assert atlas["visible_count"] == len(expected_visible(board))


def test_t016c5d_infantry_vision_radius_two():
    """Infantry class uses vision radius 2 with clear LOS."""
    assert vision_radius("infantry") == 2
    board = json.loads(board_path("ridge-02").read_text(encoding="utf-8"))
    atlas = pipeline("inf-rad", board_path("ridge-02"))
    elev = {(c["q"], c["r"]): c["elev"] for c in board["cells"]}
    for c in atlas["visible_cells"]:
        ok = False
        for u in board["units"]:
            if u["class"] != "infantry":
                continue
            o = (u["q"], u["r"])
            t = (c["q"], c["r"])
            if cube_dist(*o, *t) <= 2 and clear_los(o, t, elev):
                ok = True
        assert ok


def test_t016c5d_tower_vision_radius_three():
    """Tower class uses vision radius 3 and matches reference atlas."""
    assert vision_radius("tower") == 3
    board = json.loads(board_path("tower-03").read_text(encoding="utf-8"))
    atlas = pipeline("tower-rad", board_path("tower-03"))
    assert atlas["visible_cells"] == expected_visible(board)


def test_t016c5d_militia_default_radius_one_on_multi():
    """Militia class uses default radius 1 on multi-04."""
    board = json.loads(board_path("multi-04").read_text(encoding="utf-8"))
    militia = next(u for u in board["units"] if u["class"] == "militia")
    assert vision_radius("militia") == 1
    atlas = pipeline("militia-rad", board_path("multi-04"))
    cells = {(c["q"], c["r"]) for c in atlas["visible_cells"]}
    # militia cell itself must be visible via default radius
    assert (militia["q"], militia["r"]) in cells


def test_t016c5d_multi_unit_union_vision():
    """Multi-unit union vision matches reference and meets win condition."""
    board = json.loads(board_path("multi-04").read_text(encoding="utf-8"))
    atlas = pipeline("multi-union", board_path("multi-04"))
    assert atlas["visible_cells"] == expected_visible(board)
    assert atlas["visible_count"] >= board["target_reveal"]
    assert atlas["win_condition_met"] is True


def test_t016c5d_visible_cells_sorted_by_q_then_r():
    """Atlas visible_cells are sorted by ascending q then r."""
    atlas = pipeline("sort-qr", board_path("multi-04"))
    qs = [(c["q"], c["r"]) for c in atlas["visible_cells"]]
    assert qs == sorted(qs)


def test_t016c5d_fog_generation_starts_zero_on_load():
    """load-board starts fog_generation at 0 per turn clock contract."""
    wipe()
    run_id = "clock-load"
    assert invoke(
        [str(CLI), "load-board", "--run-id", run_id, "--board", str(board_path("plains-01"))]
    ).returncode == 0
    roster = json.loads((ROSTER_DIR / f"{run_id}.json").read_text(encoding="utf-8"))
    assert roster["fog_generation"] == 0


def test_t016c5d_fog_generation_increments_on_reveal():
    """Each reveal-fog advances fog_generation by one."""
    wipe()
    run_id = "clock-reveal"
    b = str(board_path("plains-01"))
    assert invoke([str(CLI), "load-board", "--run-id", run_id, "--board", b]).returncode == 0
    assert invoke([str(CLI), "place-units", "--run-id", run_id]).returncode == 0
    assert invoke([str(CLI), "resolve-los", "--run-id", run_id]).returncode == 0
    assert invoke([str(CLI), "reveal-fog", "--run-id", run_id]).returncode == 0
    roster = json.loads((ROSTER_DIR / f"{run_id}.json").read_text(encoding="utf-8"))
    mask = json.loads((MASK_DIR / f"{run_id}.json").read_text(encoding="utf-8"))
    assert roster["fog_generation"] == 1
    assert mask["fog_generation"] == 1
    assert invoke([str(CLI), "reveal-fog", "--run-id", run_id]).returncode == 0
    roster2 = json.loads((ROSTER_DIR / f"{run_id}.json").read_text(encoding="utf-8"))
    assert roster2["fog_generation"] == 2


def test_t016c5d_sticky_fog_keeps_cells_after_unit_removal():
    """Sticky fog keeps previously revealed cells after unit removal."""
    wipe()
    run_id = "sticky-fog"
    b = str(board_path("multi-04"))
    assert invoke([str(CLI), "load-board", "--run-id", run_id, "--board", b]).returncode == 0
    assert invoke([str(CLI), "place-units", "--run-id", run_id]).returncode == 0
    assert invoke([str(CLI), "resolve-los", "--run-id", run_id]).returncode == 0
    assert invoke([str(CLI), "reveal-fog", "--run-id", run_id]).returncode == 0
    first = json.loads((MASK_DIR / f"{run_id}.json").read_text(encoding="utf-8"))
    first_set = {(c["q"], c["r"]) for c in first["visible_cells"]}
    assert len(first_set) > 0
    roster = json.loads((ROSTER_DIR / f"{run_id}.json").read_text(encoding="utf-8"))
    roster["units"] = [u for u in roster["units"] if u["class"] == "militia"]
    (ROSTER_DIR / f"{run_id}.json").write_text(json.dumps(roster, indent=2), encoding="utf-8")
    assert invoke([str(CLI), "resolve-los", "--run-id", run_id]).returncode == 0
    assert invoke([str(CLI), "reveal-fog", "--run-id", run_id]).returncode == 0
    second = json.loads((MASK_DIR / f"{run_id}.json").read_text(encoding="utf-8"))
    second_set = {(c["q"], c["r"]) for c in second["visible_cells"]}
    assert first_set.issubset(second_set)


def test_t016c5d_empty_fog_mask_absent_before_reveal():
    """Fog mask file is absent until reveal-fog runs."""
    wipe()
    run_id = "pre-reveal"
    b = str(board_path("plains-01"))
    assert invoke([str(CLI), "load-board", "--run-id", run_id, "--board", b]).returncode == 0
    assert invoke([str(CLI), "place-units", "--run-id", run_id]).returncode == 0
    assert invoke([str(CLI), "resolve-los", "--run-id", run_id]).returncode == 0
    assert not (MASK_DIR / f"{run_id}.json").exists()


def test_t016c5d_fog_mask_snapshot_after_reveal():
    """reveal-fog writes a fog-mask snapshot under /app/work/fog-mask/."""
    wipe()
    run_id = "fog-snap"
    b = str(board_path("plains-01"))
    assert invoke([str(CLI), "load-board", "--run-id", run_id, "--board", b]).returncode == 0
    assert invoke([str(CLI), "place-units", "--run-id", run_id]).returncode == 0
    assert invoke([str(CLI), "resolve-los", "--run-id", run_id]).returncode == 0
    assert invoke([str(CLI), "reveal-fog", "--run-id", run_id]).returncode == 0
    snap = json.loads((MASK_DIR / f"{run_id}.json").read_text(encoding="utf-8"))
    assert snap["run_id"] == run_id
    assert "visible_cells" in snap
    assert snap["fog_generation"] == 1


def test_t016c5d_los_ray_ledger_rows_cover_unit_cells():
    """LOS ray ledger has one row per unit-cell pair with required fields."""
    wipe()
    run_id = "ray-ledger"
    board = json.loads(board_path("plains-01").read_text(encoding="utf-8"))
    b = str(board_path("plains-01"))
    assert invoke([str(CLI), "load-board", "--run-id", run_id, "--board", b]).returncode == 0
    assert invoke([str(CLI), "place-units", "--run-id", run_id]).returncode == 0
    assert invoke([str(CLI), "resolve-los", "--run-id", run_id]).returncode == 0
    lines = (RAY_DIR / f"{run_id}.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == len(board["units"]) * len(board["cells"])
    row = json.loads(lines[0])
    assert {"run_id", "unit_id", "q", "r", "in_radius", "clear_los"} <= set(row)


def test_t016c5d_cube_distance_reference_matches_docs():
    """Cube distance helper matches hex-cube-coordinates contract."""
    assert cube_dist(0, 0, 2, 0) == 2
    assert cube_dist(0, 0, 1, -1) == 1
    assert cube_dist(-1, 1, 1, -1) == 2


def test_t016c5d_win_condition_false_when_below_target():
    """win_condition_met is false when visible_count is below target_reveal."""
    wipe()
    run_id = "win-low"
    board = json.loads(board_path("plains-01").read_text(encoding="utf-8"))
    board["target_reveal"] = 10_000
    tmp = APP_ROOT / "work" / "tmp-high-target.json"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(board), encoding="utf-8")
    atlas = pipeline(run_id, tmp)
    assert atlas["win_condition_met"] is False
    assert atlas["visible_count"] < atlas["target_reveal"]


def test_t016c5d_tb3_board_dir_overlay_ridge():
    """TB3_BOARD_DIR overlay loads tb3-ridge and matches reference visibility."""
    env = {"TB3_BOARD_DIR": "/opt/verifier-fixtures/fogpf/boards"}
    path = board_path("tb3-ridge", env)
    assert path.exists()
    board = json.loads(path.read_text(encoding="utf-8"))
    atlas = pipeline("tb3-run", path, env)
    assert atlas["board_id"] == "tb3-ridge"
    assert atlas["visible_cells"] == expected_visible(board)
    cells = {(c["q"], c["r"]) for c in atlas["visible_cells"]}
    assert (2, 0) not in cells


def test_t016c5d_tb3_ridge_blocks_shared_far_cell():
    """Hidden /opt/verifier-fixtures tb3-ridge keeps (2,0) fogged under scout vision."""
    env = {"TB3_BOARD_DIR": "/opt/verifier-fixtures/fogpf/boards"}
    path = board_path("tb3-ridge", env)
    board = json.loads(path.read_text(encoding="utf-8"))
    elev = {(c["q"], c["r"]): c["elev"] for c in board["cells"]}
    assert clear_los((0, 0), (2, 0), elev) is False
    atlas = pipeline("tb3-block", path, env)
    cells = {(c["q"], c["r"]) for c in atlas["visible_cells"]}
    assert (2, 0) not in cells
    assert atlas["visible_cells"] == reference_visible(board)


def test_t016c5d_reset_playfield_clears_artifacts():
    """reset-playfield.sh clears roster, work, and output artifacts."""
    pipeline("reset-a", board_path("plains-01"))
    assert any(ROSTER_DIR.iterdir())
    wipe()
    assert list(ROSTER_DIR.iterdir()) == []
    assert list(OUT_DIR.iterdir()) == []


def test_t016c5d_scout_decoy_module_exists_off_hot_path():
    """scout_decoy exists but is not imported by fogpf_main."""
    decoy = APP_ROOT / "scout_decoy" / "astar.rs"
    assert decoy.is_file()
    text = decoy.read_text(encoding="utf-8")
    assert "Not invoked by fogpf CLI" in text or "not" in text.lower()
    main = (APP_ROOT / "src" / "fogpf_main.rs").read_text(encoding="utf-8")
    assert "scout_decoy" not in main


def test_t016c5d_place_units_refreshes_roster_unit_ids():
    """place-units refreshes roster unit_id list in sorted form."""
    wipe()
    run_id = "place-refresh"
    b = str(board_path("multi-04"))
    assert invoke([str(CLI), "load-board", "--run-id", run_id, "--board", b]).returncode == 0
    assert invoke([str(CLI), "place-units", "--run-id", run_id]).returncode == 0
    roster = json.loads((ROSTER_DIR / f"{run_id}.json").read_text(encoding="utf-8"))
    ids = [u["unit_id"] for u in roster["units"]]
    assert ids == sorted(ids)


def test_t016c5d_atlas_fog_generation_matches_mask_after_seal():
    """Sealed atlas fog_generation matches the fog mask value."""
    atlas = pipeline("atlas-clock", board_path("tower-03"))
    mask = json.loads((MASK_DIR / "atlas-clock.json").read_text(encoding="utf-8"))
    assert atlas["fog_generation"] == mask["fog_generation"] == 1
