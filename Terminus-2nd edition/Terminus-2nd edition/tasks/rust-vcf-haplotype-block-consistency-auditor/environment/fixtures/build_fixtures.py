"""Build seeded VCF and manifest fixtures for vcfaud."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path


def vcf_header(samples: list[str]) -> str:
    lines = [
        "##fileformat=VCFv4.2",
        '##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">',
        '##FORMAT=<ID=PS,Number=1,Type=String,Description="Phase set">',
        "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t" + "\t".join(samples),
    ]
    return "\n".join(lines) + "\n"


def bundle_body(header_samples: list[str], rows: list[str]) -> str:
    return vcf_header(header_samples) + "\n".join(rows) + "\n"


def row(chrom: str, pos: int, ref: str, alt: str, sample_gts: list[tuple[str, str]]) -> str:
    fmt_vals = [f"{gt}:{ps}" for gt, ps in sample_gts]
    return "\t".join(
        [chrom, str(pos), ".", ref, alt, "60", "PASS", ".", "GT:PS", *fmt_vals]
    )


def write_bundle(root: Path, name: str, body: str, manifest: dict) -> None:
    bundle = root / "vcf" / name
    bundle.mkdir(parents=True, exist_ok=True)
    (bundle / "variants.vcf").write_text(body, encoding="utf-8")
    profile_seed = hashlib.sha256(name.encode()).hexdigest()[:12]
    manifest = dict(manifest)
    manifest.setdefault("profile_seed", profile_seed)
    (bundle / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=4242)
    parser.add_argument("--out-dir", type=Path, default=Path("/app/fixtures"))
    args = parser.parse_args()
    rng = random.Random(args.seed)
    root = args.out_dir

    def sample_ids(n: int, prefix: str) -> list[str]:
        ids = [f"{prefix}-{rng.randint(1000, 9999)}" for _ in range(n)]
        ids.sort()
        return ids

    s_basic = sample_ids(2, "SMP")
    basic_body = bundle_body(
        s_basic,
        [
            row(
                "chr1",
                1000 + rng.randint(0, 50),
                "A",
                "G",
                [("0|1", "PS1"), ("1|0", "PS1")],
            ),
            row(
                "chr1",
                1100 + rng.randint(0, 50),
                "C",
                "T",
                [("0|1", "PS1"), ("0|1", "PS1")],
            ),
        ],
    )
    write_bundle(
        root,
        "phased-basic",
        basic_body,
        {"profile": "default", "samples": [{"sample_id": sid, "lineage_rank": i + 1} for i, sid in enumerate(s_basic)]},
    )

    s_multi = sample_ids(2, "MAL")
    multi_body = bundle_body(
        s_multi,
        [
            row(
                "chr2",
                2000 + rng.randint(0, 50),
                "G",
                "A,T",
                [("0|2", "PS9"), ("1|2", "PS9")],
            )
        ],
    )
    write_bundle(
        root,
        "multi-allelic",
        multi_body,
        {"profile": "multi", "samples": [{"sample_id": sid, "lineage_rank": i + 1} for i, sid in enumerate(s_multi)]},
    )

    s_miss = sample_ids(2, "MIS")
    miss_body = bundle_body(
        s_miss,
        [
            row(
                "chr3",
                3000 + rng.randint(0, 50),
                "T",
                "C",
                [("./.", "PS3"), (".|.", "PS3")],
            )
        ],
    )
    write_bundle(
        root,
        "missing-calls",
        miss_body,
        {"profile": "missing", "samples": [{"sample_id": sid, "lineage_rank": i + 1} for i, sid in enumerate(s_miss)]},
    )

    s_disc = sample_ids(3, "DSC")
    ps_label = f"PS{rng.randint(10, 99)}"
    disc_body = bundle_body(
        s_disc,
        [
            row(
                "chr4",
                4000 + rng.randint(0, 50),
                "A",
                "G",
                [("0|1", ps_label), ("1|0", ps_label), ("0|1", ps_label)],
            )
        ],
    )
    write_bundle(
        root,
        "cross-sample-discord",
        disc_body,
        {"profile": "discord", "samples": [{"sample_id": sid, "lineage_rank": i + 1} for i, sid in enumerate(s_disc)]},
    )

    s_mix = sample_ids(2, "MIX")
    mix_body = bundle_body(
        s_mix,
        [
            row(
                "chr5",
                5000 + rng.randint(0, 50),
                "C",
                "G",
                [("0/1", "PS5"), ("0|1", "PS5")],
            )
        ],
    )
    write_bundle(
        root,
        "unphased-mixed",
        mix_body,
        {"profile": "mixed", "samples": [{"sample_id": sid, "lineage_rank": i + 1} for i, sid in enumerate(s_mix)]},
    )

    s_dual = sample_ids(2, "DCP")
    dual_body = bundle_body(
        s_dual,
        [
            row(
                "chr1",
                1000 + rng.randint(0, 50),
                "A",
                "G",
                [("0|1", "PS-SHARED"), ("1|0", "PS-SHARED")],
            ),
            row(
                "chr2",
                2000 + rng.randint(0, 50),
                "C",
                "T",
                [("0|1", "PS-SHARED"), ("0|1", "PS-SHARED")],
            ),
        ],
    )
    write_bundle(
        root,
        "dual-chrom-ps",
        dual_body,
        {"profile": "dual-chrom", "samples": [{"sample_id": sid, "lineage_rank": i + 1} for i, sid in enumerate(s_dual)]},
    )

    catalog = {
        "bundles": [
            {"name": "phased-basic", "vcf": "variants.vcf", "manifest": "manifest.json"},
            {"name": "multi-allelic", "vcf": "variants.vcf", "manifest": "manifest.json"},
            {"name": "missing-calls", "vcf": "variants.vcf", "manifest": "manifest.json"},
            {"name": "cross-sample-discord", "vcf": "variants.vcf", "manifest": "manifest.json"},
            {"name": "unphased-mixed", "vcf": "variants.vcf", "manifest": "manifest.json"},
            {"name": "dual-chrom-ps", "vcf": "variants.vcf", "manifest": "manifest.json"},
        ]
    }
    (root / "bundle_catalog.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    print(f"fixtures written under {root}")


if __name__ == "__main__":
    main()
