"""G-026 entrypoint — subprocess vcfaud tests with haplotype reference helpers."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

APP_ROOT = Path("/app")
CLI_BIN = APP_ROOT / "bin" / "vcfaud"
RESET_SH = APP_ROOT / "scripts" / "reset-workspace.sh"
FIXTURE_ROOT = APP_ROOT / "fixtures" / "vcf"
TB3_VCF_ROOT = Path("/opt/verifier-fixtures/vcfaud/vcf")
MATRIX_DIR = APP_ROOT / "state" / "sample-phase-matrix"
EDGE_LIST_DIR = APP_ROOT / "work" / "block-edge-list"


def bundle_paths(name: str, env: dict | None = None) -> tuple[Path, Path]:
    root = Path(env["TB3_VCF_DIR"]) if env and env.get("TB3_VCF_DIR") else FIXTURE_ROOT
    bundle = root / name
    return bundle / "variants.vcf", bundle / "manifest.json"


def invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=str(APP_ROOT), capture_output=True, text=True, check=False, env=merged)


def wipe() -> None:
    proc = invoke(["bash", str(RESET_SH)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def load_edge_list(run_id: str) -> dict:
    """Parse block edge list JSONL into blocks and anomalies."""
    path = EDGE_LIST_DIR / f"{run_id}.jsonl"
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    header = json.loads(lines[0])
    blocks: dict[str, dict] = {}
    anomalies: list[dict] = []
    for line in lines[1:]:
        rec = json.loads(line)
        if rec.get("record_type") == "edge":
            bid = rec["block_id"]
            if bid not in blocks:
                blocks[bid] = {
                    "block_id": bid,
                    "chrom": rec["chrom"],
                    "ps_tag": rec["ps_tag"],
                    "variant_count": rec["variant_count"],
                    "sample_ids": [],
                }
            sid = rec["sample_id"]
            if sid not in blocks[bid]["sample_ids"]:
                blocks[bid]["sample_ids"].append(sid)
        elif rec.get("record_type") == "anomaly":
            anomalies.append(
                {
                    "anomaly_id": rec["anomaly_id"],
                    "chrom": rec["chrom"],
                    "ps_tag": rec["ps_tag"],
                    "anomaly_type": rec["anomaly_type"],
                    "sample_ids": rec["sample_ids"],
                    "variant_positions": rec["variant_positions"],
                }
            )
    block_list = sorted(blocks.values(), key=lambda b: b["block_id"])
    for block in block_list:
        block["sample_ids"] = sorted(block["sample_ids"])
    anomalies.sort(key=lambda a: a["anomaly_id"])
    return {
        "run_id": header["run_id"],
        "merge_generation": header["merge_generation"],
        "blocks": block_list,
        "anomalies": anomalies,
    }


def run_pipeline(run_id: str, bundle: str, *, env: dict | None = None) -> Path:
    vcf_path, manifest_path = bundle_paths(bundle, env)
    for step in (
        [
            str(CLI_BIN),
            "materialize",
            "--run-id",
            run_id,
            "--vcf",
            str(vcf_path),
            "--manifest",
            str(manifest_path),
        ],
        [str(CLI_BIN), "wire-blocks", "--run-id", run_id],
    ):
        proc = invoke(step, env=env)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    out = APP_ROOT / "output" / f"{run_id}-consistency-report.json"
    proc = invoke(
        [str(CLI_BIN), "score-anomalies", "--run-id", run_id, "--output", str(out)],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out


def is_phased(gt: str) -> bool:
    return "|" in gt


def is_missing(gt: str) -> bool:
    if gt in ("./.", ".|."):
        return True
    return any(part == "." for part in gt.replace("|", "/").split("/"))


def parse_alleles(gt: str) -> list[int]:
    sep = "|" if "|" in gt else "/"
    out: list[int] = []
    for part in gt.split(sep):
        if part == ".":
            continue
        out.append(int(part))
    return out


def normalize_alt(alt: str) -> list[str]:
    return [a for a in alt.split(",") if a]


def ordered_samples(manifest: dict) -> list[str]:
    return sorted(s["sample_id"] for s in manifest["samples"])


def normalize_ps(ps: str, salt: str) -> str:
    if salt and ps.startswith(salt):
        return ps[len(salt) :].lstrip("-")
    return ps


def block_key(chrom: str, ps: str, salt: str) -> str:
    return f"{chrom}:{normalize_ps(ps, salt)}"


def parse_vcf(vcf_path: Path, manifest: dict) -> list[dict[str, Any]]:
    sample_ids = ordered_samples(manifest)
    variants: list[dict[str, Any]] = []
    for line in vcf_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("#"):
            continue
        cols = line.split("\t")
        chrom, pos, _id, ref, alt = cols[0], int(cols[1]), cols[2], cols[3], cols[4]
        alt_alleles = normalize_alt(alt)
        fmt_parts = cols[8].split(":")
        gt_idx = fmt_parts.index("GT")
        ps_idx = fmt_parts.index("PS") if "PS" in fmt_parts else None
        genotypes = []
        for i, sid in enumerate(sample_ids):
            fields = cols[9 + i].split(":")
            gt_raw = fields[gt_idx]
            ps_tag = fields[ps_idx] if ps_idx is not None else ""
            genotypes.append(
                {
                    "sample_id": sid,
                    "gt_raw": gt_raw,
                    "phased": is_phased(gt_raw),
                    "missing": is_missing(gt_raw),
                    "alleles": parse_alleles(gt_raw),
                    "ps_tag": ps_tag,
                }
            )
        variants.append(
            {
                "chrom": chrom,
                "pos": pos,
                "ref_allele": ref,
                "alt_alleles": alt_alleles,
                "genotypes": genotypes,
            }
        )
    return variants


def detect_anomalies(variants: list[dict[str, Any]], salt: str = "") -> list[dict[str, Any]]:
    anomalies: list[dict[str, Any]] = []
    for v in variants:
        phased_gts = [g for g in v["genotypes"] if g["phased"] and not g["missing"]]
        if len(phased_gts) >= 2:
            patterns = {tuple(g["alleles"]) for g in phased_gts}
            if len(patterns) > 1:
                anomalies.append(
                    {
                        "anomaly_id": f"disc-{v['chrom']}-{v['pos']}",
                        "chrom": v["chrom"],
                        "ps_tag": phased_gts[0]["ps_tag"],
                        "anomaly_type": "phase_discordance",
                        "sample_ids": sorted(g["sample_id"] for g in phased_gts),
                        "variant_positions": [v["pos"]],
                    }
                )
        for g in v["genotypes"]:
            if g["missing"]:
                anomalies.append(
                    {
                        "anomaly_id": f"miss-{g['sample_id']}-{v['pos']}",
                        "chrom": v["chrom"],
                        "ps_tag": g["ps_tag"],
                        "anomaly_type": "missing_call",
                        "sample_ids": [g["sample_id"]],
                        "variant_positions": [v["pos"]],
                    }
                )
            if g["ps_tag"] and not g["phased"] and not g["missing"]:
                anomalies.append(
                    {
                        "anomaly_id": f"mix-{g['sample_id']}-{v['pos']}",
                        "chrom": v["chrom"],
                        "ps_tag": g["ps_tag"],
                        "anomaly_type": "phase_set_mixed",
                        "sample_ids": [g["sample_id"]],
                        "variant_positions": [v["pos"]],
                    }
                )
    anomalies.sort(key=lambda a: a["anomaly_id"])
    return anomalies


def build_blocks(variants: list[dict[str, Any]], salt: str = "") -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for v in variants:
        for g in v["genotypes"]:
            if not g["ps_tag"]:
                continue
            key = block_key(v["chrom"], g["ps_tag"], salt)
            groups.setdefault(key, []).append(v)
    blocks = []
    for idx, (key, vars_) in enumerate(sorted(groups.items())):
        chrom, ps_tag = key.split(":", 1)
        sample_ids = sorted({g["sample_id"] for v in vars_ for g in v["genotypes"]})
        blocks.append(
            {
                "block_id": f"blk{idx + 1:03}",
                "chrom": chrom,
                "ps_tag": ps_tag,
                "variant_count": len({v["pos"] for v in vars_}),
                "sample_ids": sample_ids,
            }
        )
    return blocks


def audit_digest(report: dict[str, Any]) -> str:
    body = json.dumps(
        {
            "anomaly_count": report["anomaly_count"],
            "block_count": report["block_count"],
            "block_ids": sorted(b["block_id"] for b in report["blocks"]),
            "run_id": report["run_id"],
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(body.encode()).hexdigest()


def reference_audit(
    run_id: str,
    vcf_path: Path,
    manifest_path: Path,
    *,
    ps_salt: str = "",
    ingest_generation: int = 1,
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    variants = parse_vcf(vcf_path, manifest)
    blocks = build_blocks(variants, ps_salt)
    anomalies = detect_anomalies(variants, ps_salt)
    report = {
        "run_id": run_id,
        "block_count": len(blocks),
        "anomaly_count": len(anomalies),
        "blocks": blocks,
        "anomalies": anomalies,
    }
    report["audit_digest"] = audit_digest(report)
    report["ingest_generation"] = ingest_generation
    return report



@pytest.fixture(autouse=True)
def isolate_workspace():
    wipe()
    yield
    wipe()

class TestVcfaudHaplotypeContracts:
    def test_contract_01_phased_digest(self):
        """Phased-basic bundle audit digest must match independent reference."""
        run_id = "run-phased-basic"
        vcf, manifest = (
            FIXTURE_ROOT / "phased-basic" / "variants.vcf",
            FIXTURE_ROOT / "phased-basic" / "manifest.json",
        )
        out = run_pipeline(run_id, "phased-basic")
        rep = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_audit(run_id, vcf, manifest)
        assert rep["audit_digest"] == ref["audit_digest"]
        assert rep["block_count"] == ref["block_count"]

    def test_contract_02_pipe_separator(self):
        """Unphased slash GT under PS must emit phase_set_mixed anomaly."""
        run_id = "run-unphased-mixed"
        vcf, manifest = (
            FIXTURE_ROOT / "unphased-mixed" / "variants.vcf",
            FIXTURE_ROOT / "unphased-mixed" / "manifest.json",
        )
        out = run_pipeline(run_id, "unphased-mixed")
        rep = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_audit(run_id, vcf, manifest)
        assert rep["audit_digest"] == ref["audit_digest"]
        assert rep["anomalies"] == ref["anomalies"]

    def test_contract_03_multi_alt(self):
        """Multi-allelic VCF must expose two ALT alleles in sample matrix."""
        run_id = "run-multi-alt"
        run_pipeline(run_id, "multi-allelic")
        matrix = json.loads(
            (APP_ROOT / "state" / "sample-phase-matrix" / f"{run_id}.json").read_text(encoding="utf-8")
        )
        alts = matrix["variant_catalog"][0]["alt_alleles"]
        assert len(alts) == 2

    def test_contract_04_missing_calls(self):
        """Missing-call bundle must flag both ./. and .|. genotypes."""
        run_id = "run-missing"
        vcf, manifest = (
            FIXTURE_ROOT / "missing-calls" / "variants.vcf",
            FIXTURE_ROOT / "missing-calls" / "manifest.json",
        )
        out = run_pipeline(run_id, "missing-calls")
        rep = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_audit(run_id, vcf, manifest)
        assert rep["anomaly_count"] == ref["anomaly_count"]
        assert rep["anomaly_count"] >= 2
        assert rep["audit_digest"] == ref["audit_digest"]
        assert rep["anomalies"] == ref["anomalies"]

    def test_contract_05_discord(self):
        """Cross-sample discord bundle must emit phase_discordance anomaly."""
        run_id = "run-discord"
        vcf, manifest = (
            FIXTURE_ROOT / "cross-sample-discord" / "variants.vcf",
            FIXTURE_ROOT / "cross-sample-discord" / "manifest.json",
        )
        out = run_pipeline(run_id, "cross-sample-discord")
        rep = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_audit(run_id, vcf, manifest)
        assert rep["audit_digest"] == ref["audit_digest"]
        assert rep["anomalies"] == ref["anomalies"]

    def test_contract_06_lineage_order(self):
        """Sample matrix sample_lineage must sort sample ids ascending."""
        run_id = "run-lineage"
        run_pipeline(run_id, "phased-basic")
        matrix = json.loads(
            (APP_ROOT / "state" / "sample-phase-matrix" / f"{run_id}.json").read_text(encoding="utf-8")
        )
        assert matrix["sample_lineage"] == sorted(matrix["sample_lineage"])

    def test_contract_07_block_group(self):
        """Shared PS tag on different chromosomes must form separate blocks."""
        run_id = "run-blocks"
        run_pipeline(run_id, "dual-chrom-ps")
        ledger = load_edge_list(run_id)
        assert len(ledger["blocks"]) == 2
        chroms = {b["chrom"] for b in ledger["blocks"]}
        assert chroms == {"chr1", "chr2"}
        ps_tags = {b["ps_tag"] for b in ledger["blocks"]}
        assert ps_tags == {"PS-SHARED"}
        for block in ledger["blocks"]:
            assert block["ps_tag"]
            assert block["variant_count"] >= 1

    def test_contract_08_anom_sort(self):
        """Exported anomalies must sort by anomaly_id ascending."""
        run_id = "run-anom-sort"
        out = run_pipeline(run_id, "missing-calls")
        rep = json.loads(out.read_text(encoding="utf-8"))
        ids = [a["anomaly_id"] for a in rep["anomalies"]]
        assert ids == sorted(ids)

    def test_contract_09_block_count(self):
        """Report block_count must equal blocks array length."""
        run_id = "run-block-count"
        out = run_pipeline(run_id, "phased-basic")
        rep = json.loads(out.read_text(encoding="utf-8"))
        assert rep["block_count"] == len(rep["blocks"])

    def test_contract_10_anom_count(self):
        """Report anomaly_count must equal anomalies array length."""
        run_id = "run-anom-count"
        out = run_pipeline(run_id, "cross-sample-discord")
        rep = json.loads(out.read_text(encoding="utf-8"))
        assert rep["anomaly_count"] == len(rep["anomalies"])

    def test_contract_11_decoy_path(self):
        """Decoy PCA heatmap module must not be required for materialize wire score."""
        run_id = "run-decoy"
        out = run_pipeline(run_id, "phased-basic")
        assert out.exists()

    def test_contract_12_output_suffix(self):
        """Score-anomalies must write caller path under /app/output with consistency-report suffix."""
        run_id = "run-out-name"
        out = run_pipeline(run_id, "phased-basic")
        assert out.name == f"{run_id}-consistency-report.json"
        assert out.parent == APP_ROOT / "output"

    def test_contract_13_profile_field(self):
        """Sample phase matrix must copy manifest profile into profile field."""
        run_id = "run-profile"
        run_pipeline(run_id, "multi-allelic")
        matrix = json.loads(
            (APP_ROOT / "state" / "sample-phase-matrix" / f"{run_id}.json").read_text(encoding="utf-8")
        )
        assert matrix["profile"] == "multi"


class TestSampleMatrixGeneration:
    def test_contract_14_staging_snap(self):
        """Materialize ingest stage must write staging snapshot JSON under sample-phase-matrix."""
        run_id = "run-staging-snapshot"
        run_pipeline(run_id, "phased-basic")
        snap = APP_ROOT / "state" / "sample-phase-matrix" / f"{run_id}.json"
        assert snap.is_file()
        matrix = json.loads(snap.read_text(encoding="utf-8"))
        assert matrix["run_id"] == run_id
        assert matrix["variant_catalog"]

    def test_contract_15_ingest_gen(self):
        """First materialize ingest stage must record ingest_generation one in staging snapshot."""
        run_id = "run-ingest-gen"
        run_pipeline(run_id, "phased-basic")
        matrix = json.loads(
            (APP_ROOT / "state" / "sample-phase-matrix" / f"{run_id}.json").read_text(encoding="utf-8")
        )
        assert matrix["ingest_generation"] == 1

    def test_contract_16_reingest_gen(self):
        """Re-materialize of same run id must increment ingest_generation."""
        run_id = "run-reingest"
        run_pipeline(run_id, "phased-basic")
        vcf = FIXTURE_ROOT / "phased-basic" / "variants.vcf"
        manifest = FIXTURE_ROOT / "phased-basic" / "manifest.json"
        invoke(
            [
                str(CLI_BIN),
                "materialize",
                "--run-id",
                run_id,
                "--vcf",
                str(vcf),
                "--manifest",
                str(manifest),
            ]
        )
        matrix = json.loads(
            (APP_ROOT / "state" / "sample-phase-matrix" / f"{run_id}.json").read_text(encoding="utf-8")
        )
        assert matrix["ingest_generation"] == 2

    def test_contract_17_merge_gen(self):
        """First wire-blocks export prep must record merge_generation one in staging edge list meta."""
        run_id = "run-merge-gen"
        run_pipeline(run_id, "phased-basic")
        ledger = load_edge_list(run_id)
        assert ledger["merge_generation"] == 1


class TestVcfaudHiddenProbes:
    def test_contract_18_tb3_digest(self):
        """TB3_PS_SALT must strip prefix before PS block grouping."""
        tb3_root = TB3_VCF_ROOT
        run_id = "run-tb3-salt"
        env = {"TB3_PS_SALT": "SALT", "TB3_VCF_DIR": str(tb3_root)}
        vcf = tb3_root / "tb3-ps-salt" / "variants.vcf"
        manifest = tb3_root / "tb3-ps-salt" / "manifest.json"
        out = run_pipeline(run_id, "tb3-ps-salt", env=env)
        rep = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_audit(run_id, vcf, manifest, ps_salt="SALT")
        assert rep["audit_digest"] == ref["audit_digest"]

    def test_contract_19_tb3_ps_tag(self):
        """Without TB3_PS_SALT, exported block ps_tag must retain the SALT prefix."""
        tb3_root = TB3_VCF_ROOT
        with_salt = run_pipeline(
            "run-salt-on",
            "tb3-ps-salt",
            env={"TB3_VCF_DIR": str(tb3_root), "TB3_PS_SALT": "SALT"},
        )
        without_salt = run_pipeline(
            "run-salt-off",
            "tb3-ps-salt",
            env={"TB3_VCF_DIR": str(tb3_root)},
        )
        rep_on = json.loads(with_salt.read_text(encoding="utf-8"))
        rep_off = json.loads(without_salt.read_text(encoding="utf-8"))
        assert rep_on["blocks"][0]["ps_tag"] == "77"
        assert rep_off["blocks"][0]["ps_tag"] == "SALT-77"
