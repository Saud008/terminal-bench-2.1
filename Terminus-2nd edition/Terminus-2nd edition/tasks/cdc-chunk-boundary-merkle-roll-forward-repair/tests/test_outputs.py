"""Verifier tests for CDC chunk merkle roll-forward."""



from __future__ import annotations



import json

import subprocess

from pathlib import Path



import pytest



from reference_roll import (

    checkpoint_from_state,

    chunk_id,

    craft_min_chunk_payload,

    inject_byte,

    max_chunk_length,

    params_for_seed,

    reference_roll,

    simulate_roll,

)



APP = Path("/app")

FIX = APP / "fixtures" / "binaries"

SEEDS = json.loads((APP / "config" / "seeds.json").read_text(encoding="utf-8"))["seeds"]



# Representative matrix only — full cross-product was trivially solved by agents.

CORE_ROLL_CASES = [

    ("baseline.bin", "alpha01"),

    ("boundary.bin", "roll7c"),

    ("oddleaf.bin", "beta22"),

    ("resume.bin", "cdc9f"),

    ("sparse.bin", "mix4e"),

]



def run_roll(

    fixture: str,

    seed: str,

    output: Path,

    *,

    checkpoint: Path | None = None,

    resume: bool = False,

    max_chunks: int = 0,

    data_path: Path | None = None,

) -> subprocess.CompletedProcess:

    input_path = data_path or (FIX / fixture)

    cmd = [

        "/usr/local/bin/cdcctl",

        "roll",

        "--input",

        str(input_path),

        "--seed",

        seed,

        "--output",

        str(output),

    ]

    if checkpoint is not None:

        cmd.extend(["--checkpoint", str(checkpoint)])

    if resume:

        cmd.append("--resume")

    if max_chunks:

        cmd.extend(["--max-chunks", str(max_chunks)])

    return subprocess.run(cmd, capture_output=True, text=True)





class TestCdcRoll:

    def test_fixture_catalog_present(self):

        for name in ("baseline.bin", "repeat.bin", "sparse.bin", "resume.bin", "boundary.bin", "oddleaf.bin"):

            assert (FIX / name).is_file()



    @pytest.mark.parametrize("fixture,seed", CORE_ROLL_CASES)

    def test_roll_matches_reference(self, fixture, seed):

        case = f"{seed}-{fixture}"

        out = APP / "output" / f"ref-{case}.json"

        cp = APP / "state" / f"cp-{case}.json"

        proc = run_roll(fixture, seed, out, checkpoint=cp)

        assert proc.returncode == 0, proc.stderr + proc.stdout

        got = json.loads(out.read_text(encoding="utf-8"))

        data = (FIX / fixture).read_bytes()

        exp = reference_roll(data, seed, fixture)

        assert got == exp



    def test_no_chunk_exceeds_max(self):

        fixture = "repeat.bin"

        seed = SEEDS[0]

        p = params_for_seed(seed)

        out = APP / "output" / "max-repeat.json"

        proc = run_roll(fixture, seed, out, checkpoint=APP / "state" / "max-cp.json")

        assert proc.returncode == 0, proc.stderr

        got = json.loads(out.read_text(encoding="utf-8"))

        assert max_chunk_length(got["chunks"]) <= p.max_chunk



    def test_merkle_order_sensitive(self):

        seed = "alpha01"

        fixture = "baseline.bin"

        out = APP / "output" / "merkle-order.json"

        proc = run_roll(fixture, seed, out, checkpoint=APP / "state" / "merkle-cp.json")

        assert proc.returncode == 0, proc.stderr

        got = json.loads(out.read_text(encoding="utf-8"))

        exp = reference_roll((FIX / fixture).read_bytes(), seed, fixture)

        assert got["merkle_root"] == exp["merkle_root"]



    def test_merkle_odd_leaf_duplicates_last(self):

        seed = "beta22"

        fixture = "oddleaf.bin"

        out = APP / "output" / "merkle-odd.json"

        proc = run_roll(fixture, seed, out, checkpoint=APP / "state" / "merkle-odd-cp.json")

        assert proc.returncode == 0, proc.stderr

        got = json.loads(out.read_text(encoding="utf-8"))

        exp = reference_roll((FIX / fixture).read_bytes(), seed, fixture)

        assert len(got["chunks"]) == 3

        assert got["merkle_root"] == exp["merkle_root"]



    def test_resume_from_checkpoint(self):

        fixture = "resume.bin"

        seed = "roll7c"

        cp = APP / "state" / "resume-cp.json"

        partial = APP / "output" / "resume-partial.json"

        final = APP / "output" / "resume-final.json"

        subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)

        p1 = run_roll(fixture, seed, partial, checkpoint=cp, max_chunks=4)

        assert p1.returncode == 0, p1.stderr + p1.stdout

        assert cp.is_file()

        p2 = run_roll(fixture, seed, final, checkpoint=cp, resume=True)

        assert p2.returncode == 0, p2.stderr + p2.stdout

        got = json.loads(final.read_text(encoding="utf-8"))

        exp = reference_roll((FIX / fixture).read_bytes(), seed, fixture)

        exp["resumed"] = True

        assert got == exp



    def test_double_resume_matches_reference(self):

        fixture = "boundary.bin"

        seed = "cdc9f"

        cp = APP / "state" / "double-resume-cp.json"

        subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)

        p1 = run_roll(fixture, seed, APP / "output" / "dr-p1.json", checkpoint=cp, max_chunks=3)

        assert p1.returncode == 0, p1.stderr + p1.stdout

        p2 = run_roll(

            fixture,

            seed,

            APP / "output" / "dr-p2.json",

            checkpoint=cp,

            resume=True,

            max_chunks=4,

        )

        assert p2.returncode == 0, p2.stderr + p2.stdout

        p3 = run_roll(

            fixture,

            seed,

            APP / "output" / "dr-final.json",

            checkpoint=cp,

            resume=True,

        )

        assert p3.returncode == 0, p3.stderr + p3.stdout

        got = json.loads((APP / "output" / "dr-final.json").read_text(encoding="utf-8"))

        data = (FIX / fixture).read_bytes()

        exp = reference_roll(data, seed, fixture)

        exp["resumed"] = True

        assert got == exp



    def test_checkpoint_offset_is_next_byte_index(self):

        fixture = "resume.bin"

        seed = "mix4e"

        cp = APP / "state" / "offset-cp.json"

        subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)

        proc = run_roll(

            fixture,

            seed,

            APP / "output" / "offset-partial.json",

            checkpoint=cp,

            max_chunks=5,

        )

        assert proc.returncode == 0, proc.stderr + proc.stdout

        saved = json.loads(cp.read_text(encoding="utf-8"))

        data = (FIX / fixture).read_bytes()

        exp_state = simulate_roll(data, seed, max_new_chunks=5)

        assert saved["offset"] == exp_state.offset



    def test_resume_window_affects_next_boundary(self):

        fixture = "boundary.bin"

        seed = "roll7c"

        cp = APP / "state" / "window-cp.json"

        subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)

        proc = run_roll(

            fixture,

            seed,

            APP / "output" / "window-partial.json",

            checkpoint=cp,

            max_chunks=2,

        )

        assert proc.returncode == 0, proc.stderr + proc.stdout

        partial_cp = json.loads(cp.read_text(encoding="utf-8"))

        assert partial_cp.get("window") != ""

        final = APP / "output" / "window-final.json"

        proc = run_roll(fixture, seed, final, checkpoint=cp, resume=True)

        assert proc.returncode == 0, proc.stderr + proc.stdout

        got = json.loads(final.read_text(encoding="utf-8"))

        exp = reference_roll((FIX / fixture).read_bytes(), seed, fixture)

        exp["resumed"] = True

        assert got == exp



    def test_seed_byte_injection(self):

        fixture = "baseline.bin"

        seed = "cdc9f"

        raw = (FIX / fixture).read_bytes()

        mutated = inject_byte(raw, seed)

        tmp = APP / "output" / "injected.bin"

        tmp.write_bytes(mutated)

        out = APP / "output" / "injected-roll.json"

        proc = run_roll(fixture, seed, out, checkpoint=APP / "state" / "inj-cp.json", data_path=tmp)

        assert proc.returncode == 0, proc.stderr

        got = json.loads(out.read_text(encoding="utf-8"))

        exp = reference_roll(mutated, seed, "injected.bin")

        assert got == exp



    def test_chunk_ids_include_offset(self):

        seed = "mix4e"

        fixture = "repeat.bin"

        out = APP / "output" / "ids.json"

        proc = run_roll(fixture, seed, out, checkpoint=APP / "state" / "ids-cp.json")

        assert proc.returncode == 0, proc.stderr

        got = json.loads(out.read_text(encoding="utf-8"))

        data = (FIX / fixture).read_bytes()

        exp = reference_roll(data, seed, fixture)

        for got_chunk, exp_chunk in zip(got["chunks"], exp["chunks"], strict=True):

            assert got_chunk["id"] == exp_chunk["id"]

            assert got_chunk["id"] == chunk_id(

                seed,

                got_chunk["offset"],

                data[got_chunk["offset"] : got_chunk["offset"] + got_chunk["length"]],

            )



    def test_min_chunk_defers_early_boundary(self):

        seed = "alpha01"

        data = craft_min_chunk_payload(seed)

        tmp = APP / "output" / "min-chunk.bin"

        tmp.write_bytes(data)

        out = APP / "output" / "min-chunk.json"

        proc = run_roll(

            "baseline.bin",

            seed,

            out,

            checkpoint=APP / "state" / "min-cp.json",

            data_path=tmp,

        )

        assert proc.returncode == 0, proc.stderr

        got = json.loads(out.read_text(encoding="utf-8"))

        exp = reference_roll(data, seed, "min-chunk.bin")

        assert got == exp



    def test_fresh_roll_ignores_complete_checkpoint(self):

        fixture = "sparse.bin"

        seed = "alpha01"

        cp = APP / "state" / "fresh-ignore-cp.json"

        subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)

        p1 = run_roll(fixture, seed, APP / "output" / "fresh-ignore-p1.json", checkpoint=cp)

        assert p1.returncode == 0, p1.stderr + p1.stdout

        complete = json.loads(cp.read_text(encoding="utf-8"))

        assert complete.get("complete") is True

        p2 = run_roll(fixture, seed, APP / "output" / "fresh-ignore-p2.json", checkpoint=cp)

        assert p2.returncode == 0, p2.stderr + p2.stdout

        got = json.loads((APP / "output" / "fresh-ignore-p2.json").read_text(encoding="utf-8"))

        data = (FIX / fixture).read_bytes()

        exp = reference_roll(data, seed, fixture)

        assert got == exp

        assert got["resumed"] is False



    def test_resume_leaf_count_matches_chunks(self):

        fixture = "boundary.bin"

        seed = "roll7c"

        cp = APP / "state" / "leaf-count-cp.json"

        subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)

        p1 = run_roll(fixture, seed, APP / "output" / "leaf-count-p1.json", checkpoint=cp, max_chunks=2)

        assert p1.returncode == 0, p1.stderr + p1.stdout

        partial = json.loads(cp.read_text(encoding="utf-8"))

        assert len(partial["leaves"]) == len(partial["chunks"])

        p2 = run_roll(fixture, seed, APP / "output" / "leaf-count-final.json", checkpoint=cp, resume=True)

        assert p2.returncode == 0, p2.stderr + p2.stdout

        final_cp = json.loads(cp.read_text(encoding="utf-8"))

        assert len(final_cp["leaves"]) == len(final_cp["chunks"])

        got = json.loads((APP / "output" / "leaf-count-final.json").read_text(encoding="utf-8"))

        exp = reference_roll((FIX / fixture).read_bytes(), seed, fixture)

        exp["resumed"] = True

        assert got == exp



    def test_checkpoint_chunk_start_restored_on_resume(self):

        fixture = "boundary.bin"

        seed = "cdc9f"

        data = (FIX / fixture).read_bytes()

        cp = APP / "state" / "chunk-start-cp.json"

        subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)

        proc = run_roll(

            fixture,

            seed,

            APP / "output" / "chunk-start-partial.json",

            checkpoint=cp,

            max_chunks=2,

        )

        assert proc.returncode == 0, proc.stderr + proc.stdout

        partial = json.loads(cp.read_text(encoding="utf-8"))

        exp_partial = simulate_roll(data, seed, max_new_chunks=2)

        assert partial["chunk_start"] == exp_partial.chunk_start

        proc = run_roll(

            fixture,

            seed,

            APP / "output" / "chunk-start-final.json",

            checkpoint=cp,

            resume=True,

        )

        assert proc.returncode == 0, proc.stderr + proc.stdout

        got = json.loads((APP / "output" / "chunk-start-final.json").read_text(encoding="utf-8"))

        exp = reference_roll(data, seed, fixture)

        exp["resumed"] = True

        assert got == exp



    def test_config_target_affects_boundaries(self):

        fixture = "repeat.bin"

        seed = "beta22"

        data = (FIX / fixture).read_bytes()

        out = APP / "output" / "target-roll.json"

        proc = run_roll(fixture, seed, out, checkpoint=APP / "state" / "target-cp.json")

        assert proc.returncode == 0, proc.stderr

        got = json.loads(out.read_text(encoding="utf-8"))

        exp = reference_roll(data, seed, fixture)

        assert got["chunk_count"] == exp["chunk_count"]

        assert got["chunks"][0]["offset"] == exp["chunks"][0]["offset"]




class TestRollAntiCheat:

    """CLI-only anti-cheat: no internal source swaps; behavior via cdcctl roll only."""



    def test_phased_resume_matches_reference(self):

        """Multi-phase --max-chunks then --resume must match independent phased reference."""

        fixture = "boundary.bin"

        seed = "cdc9f"

        data = (FIX / fixture).read_bytes()

        cp = APP / "state" / "anti-phased-cp.json"

        subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)

        p1 = run_roll(

            fixture,

            seed,

            APP / "output" / "anti-phased-p1.json",

            checkpoint=cp,

            max_chunks=2,

        )

        assert p1.returncode == 0, p1.stderr + p1.stdout

        p2 = run_roll(

            fixture,

            seed,

            APP / "output" / "anti-phased-final.json",

            checkpoint=cp,

            resume=True,

        )

        assert p2.returncode == 0, p2.stderr + p2.stdout

        got = json.loads((APP / "output" / "anti-phased-final.json").read_text(encoding="utf-8"))

        exp = reference_roll(data, seed, fixture)

        exp["resumed"] = True

        assert got == exp



    def test_max_chunks_partial_skips_output_file(self):

        """Partial --max-chunks roll must not write --output when stopped mid-stream."""

        fixture = "resume.bin"

        seed = "roll7c"

        data = (FIX / fixture).read_bytes()

        output = APP / "output" / "max-chunks-skip-output.json"

        cp = APP / "state" / "max-chunks-skip-output-cp.json"

        full_count = reference_roll(data, seed, fixture)["chunk_count"]

        assert full_count > 4

        subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)

        proc = run_roll(fixture, seed, output, checkpoint=cp, max_chunks=4)

        assert proc.returncode == 0, proc.stderr + proc.stdout

        assert not output.is_file()

        partial_cp = json.loads(cp.read_text(encoding="utf-8"))

        assert partial_cp.get("complete") is False

        assert len(partial_cp.get("chunks", [])) < full_count



    def test_max_chunks_resume_completes_roll(self):

        """--max-chunks with resume must eventually produce the full reference roll."""

        fixture = "resume.bin"

        seed = "roll7c"

        data = (FIX / fixture).read_bytes()

        cp = APP / "state" / "anti-max-cp.json"

        full_count = reference_roll(data, seed, fixture)["chunk_count"]

        subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)

        p1 = run_roll(

            fixture,

            seed,

            APP / "output" / "anti-max-p1.json",

            checkpoint=cp,

            max_chunks=4,

        )

        assert p1.returncode == 0, p1.stderr + p1.stdout

        partial_cp = json.loads(cp.read_text(encoding="utf-8"))

        assert len(partial_cp.get("chunks", [])) < full_count

        p2 = run_roll(

            fixture,

            seed,

            APP / "output" / "anti-max-final.json",

            checkpoint=cp,

            resume=True,

        )

        assert p2.returncode == 0, p2.stderr + p2.stdout

        got = json.loads((APP / "output" / "anti-max-final.json").read_text(encoding="utf-8"))

        exp = reference_roll(data, seed, fixture)

        exp["resumed"] = True

        assert got == exp



    def test_checkpoint_window_matches_reference(self):

        """Checkpoint rolling-window serialization must match reference simulation."""

        fixture = "boundary.bin"

        seed = "roll7c"

        data = (FIX / fixture).read_bytes()

        cp = APP / "state" / "anti-window-cp.json"

        subprocess.run(["bash", str(APP / "scripts" / "reset-state.sh")], check=True)

        proc = run_roll(

            fixture,

            seed,

            APP / "output" / "anti-window-partial.json",

            checkpoint=cp,

            max_chunks=2,

        )

        assert proc.returncode == 0, proc.stderr + proc.stdout

        saved = json.loads(cp.read_text(encoding="utf-8"))

        exp_state = simulate_roll(data, seed, max_new_chunks=2)

        exp_cp = checkpoint_from_state(exp_state, fixture, seed)

        assert saved["window"] == exp_cp["window"]

        assert saved["chunk_start"] == exp_cp["chunk_start"]

        assert saved["offset"] == exp_cp["offset"]



    def test_seed_changes_partition(self):

        """Anti-hardcode: same fixture with different seeds must match per-seed reference."""

        fixture = "repeat.bin"

        data = (FIX / fixture).read_bytes()

        out_a = APP / "output" / "anti-seed-a.json"

        out_b = APP / "output" / "anti-seed-b.json"

        proc_a = run_roll(fixture, "alpha01", out_a, checkpoint=APP / "state" / "anti-seed-a-cp.json")

        proc_b = run_roll(fixture, "beta22", out_b, checkpoint=APP / "state" / "anti-seed-b-cp.json")

        assert proc_a.returncode == 0, proc_a.stderr + proc_a.stdout

        assert proc_b.returncode == 0, proc_b.stderr + proc_b.stdout

        got_a = json.loads(out_a.read_text(encoding="utf-8"))

        got_b = json.loads(out_b.read_text(encoding="utf-8"))

        exp_a = reference_roll(data, "alpha01", fixture)

        exp_b = reference_roll(data, "beta22", fixture)

        assert got_a == exp_a

        assert got_b == exp_b

        assert got_a["merkle_root"] != got_b["merkle_root"] or got_a["chunks"] != got_b["chunks"]

