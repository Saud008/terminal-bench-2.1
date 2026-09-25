"""Generate signed policy bundles and trust material (build-time only)."""
from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLES = ROOT / "fixtures" / "bundles"
TRUST = ROOT / "trust"
BUILD_SEED = "opa-bundle-signature-digest-chain-verifier"

KEYS = {
    "alpha": "key-material-alpha-32bytes-long!!",
    "beta": "key-material-beta-32bytes-long!!!",
}


def tag_numeric(seed: str) -> int:
    h = hashlib.sha256(f"{BUILD_SEED}:{seed}".encode()).digest()
    return ((h[0] << 8) | h[1]) % 900 + 100


def apply_threshold(content: str, seed: str) -> str:
    return content.replace("__THRESHOLD__", str(tag_numeric(seed)))


def canonical(path: str) -> str:
    p = path.replace("\\", "/").removeprefix("./")
    parts: list[str] = []
    for part in p.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return "/".join(parts)


def member_digest(content: bytes) -> bytes:
    return hashlib.sha256(content).digest()


def chain_root(members: list[tuple[str, bytes]]) -> str:
    ordered = sorted(((canonical(p), b) for p, b in members), key=lambda x: x[0])
    state = hashlib.sha256(b"").digest()
    for path, body in ordered:
        fd = member_digest(body)
        h = hashlib.sha256()
        h.update(state)
        h.update(path.encode())
        h.update(fd)
        state = h.digest()
    return state.hex()


def scoped_root(members: list[tuple[str, bytes]], scope: str) -> str:
    subset = [(p, b) for p, b in members if canonical(p).startswith(scope)]
    return chain_root(subset)


def sign(scope: str, chain_hex: str, key_id: str) -> str:
    mac = hmac.new(KEYS[key_id].encode(), digestmod=hashlib.sha256)
    mac.update(scope.encode())
    mac.update(chain_hex.encode())
    return mac.hexdigest()


def write_bundle(name: str, manifest: dict, files: dict[str, str], signatures: list[dict]) -> None:
    bdir = BUNDLES / name
    bdir.mkdir(parents=True, exist_ok=True)
    (bdir / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for rel, content in files.items():
        path = bdir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    sig = {"signatures": signatures}
    (bdir / ".signatures.json").write_text(json.dumps(sig, indent=2) + "\n", encoding="utf-8")


def member_bytes(files: dict[str, str], manifest_members: list[str]) -> list[tuple[str, bytes]]:
    out: list[tuple[str, bytes]] = []
    for raw in manifest_members:
        if raw in ("MANIFEST.json", ".signatures.json"):
            continue
        out.append((raw, files[raw].encode()))
    return out


def good_allow_basic() -> None:
    data = '{"foo": 950}\n'
    policy = (
        "package policy\n\n"
        "default allow = false\n\n"
        "allow { data.foo >= input.threshold }\n"
    )
    manifest = {
        "revision": "1",
        "roots": ["policies/", "data/"],
        "members": ["policies/allow.rego", "data/data.json", "MANIFEST.json", ".signatures.json"],
    }
    files = {"data/data.json": data, "policies/allow.rego": policy}
    members = member_bytes(files, manifest["members"])
    sigs = [
        {
            "key_id": "alpha",
            "scope": "policies/",
            "chain_root": scoped_root(members, "policies/"),
            "signature": sign("policies/", scoped_root(members, "policies/"), "alpha"),
        },
        {
            "key_id": "alpha",
            "scope": "data/",
            "chain_root": scoped_root(members, "data/"),
            "signature": sign("data/", scoped_root(members, "data/"), "alpha"),
        },
    ]
    write_bundle("allow-basic", manifest, files, sigs)
    (BUNDLES / "allow-basic" / "input").mkdir(exist_ok=True)
    (BUNDLES / "allow-basic" / "input/default.json").write_text('{"threshold": "__THRESHOLD__"}\n', encoding="utf-8")


def good_deny_edge() -> None:
    data = '{"foo": 1}\n'
    policy = (
        "package policy\n\n"
        "default allow = false\n\n"
        "allow { input.threshold > 100 }\n"
    )
    manifest = {
        "revision": "1",
        "roots": ["policies/", "data/"],
        "members": ["policies/allow.rego", "data/data.json", "MANIFEST.json", ".signatures.json"],
    }
    files = {"data/data.json": data, "policies/allow.rego": policy}
    members = member_bytes(files, manifest["members"])
    sigs = [
        {
            "key_id": "alpha",
            "scope": "policies/",
            "chain_root": scoped_root(members, "policies/"),
            "signature": sign("policies/", scoped_root(members, "policies/"), "alpha"),
        }
    ]
    write_bundle("deny-edge", manifest, files, sigs)
    (BUNDLES / "deny-edge" / "input").mkdir(exist_ok=True)
    (BUNDLES / "deny-edge" / "input/default.json").write_text('{"threshold": 5}\n', encoding="utf-8")


def good_multi_scope() -> None:
    data = '{"foo": 950}\n'
    data_z = '{"meta": "z"}\n'
    data_a = '{"meta": "a"}\n'
    policy = "package policy\n\ndefault allow = false\n\nallow { data.foo >= input.threshold }\n"
    manifest = {
        "revision": "1",
        "roots": ["policies/", "data/"],
        # data/ members listed in manifest order (not lexicographic) so digest
        # chain order is discriminating for scoped verification.
        "members": [
            "policies/allow.rego",
            "data/data.json",
            "data/z-extra.json",
            "data/a-extra.json",
            "MANIFEST.json",
            ".signatures.json",
        ],
    }
    files = {
        "data/data.json": data,
        "data/z-extra.json": data_z,
        "data/a-extra.json": data_a,
        "policies/allow.rego": policy,
    }
    members = member_bytes(files, manifest["members"])
    sigs = [
        {
            "key_id": "alpha",
            "scope": "policies/",
            "chain_root": scoped_root(members, "policies/"),
            "signature": sign("policies/", scoped_root(members, "policies/"), "alpha"),
        },
        {
            "key_id": "alpha",
            "scope": "data/",
            "chain_root": scoped_root(members, "data/"),
            "signature": sign("data/", scoped_root(members, "data/"), "alpha"),
        },
    ]
    write_bundle("multi-scope", manifest, files, sigs)
    (BUNDLES / "multi-scope" / "input").mkdir(exist_ok=True)
    (BUNDLES / "multi-scope" / "input/default.json").write_text('{"threshold": "__THRESHOLD__"}\n', encoding="utf-8")


def path_normalize() -> None:
    data = '{"foo": 900}\n'
    policy = "package policy\n\ndefault allow = false\n\nallow { data.foo >= input.threshold }\n"
    manifest = {
        "revision": "1",
        "roots": ["policies/", "data/"],
        "members": [
            "./data/../data/data.json",
            "policies/allow.rego",
            "MANIFEST.json",
            ".signatures.json",
        ],
    }
    files = {"data/data.json": data, "policies/allow.rego": policy}
    members = member_bytes(files, ["data/data.json", "policies/allow.rego"])
    sigs = [
        {
            "key_id": "alpha",
            "scope": "data/",
            "chain_root": scoped_root(members, "data/"),
            "signature": sign("data/", scoped_root(members, "data/"), "alpha"),
        }
    ]
    write_bundle("path-normalize", manifest, files, sigs)
    (BUNDLES / "path-normalize" / "input").mkdir(exist_ok=True)
    (BUNDLES / "path-normalize" / "input/default.json").write_text('{"threshold": "__THRESHOLD__"}\n', encoding="utf-8")


def trap_tampered() -> None:
    good_allow_basic()
    bdir = BUNDLES / "tampered-member"
    if bdir.exists():
        import shutil

        shutil.rmtree(bdir)
    import shutil

    shutil.copytree(BUNDLES / "allow-basic", bdir)
    data_path = bdir / "data/data.json"
    data_path.write_text('{"foo": 99999}\n', encoding="utf-8")


def trap_revoked() -> None:
    data = '{"foo": 3}\n'
    policy = "package policy\n\ndefault allow = false\n\nallow { data.foo >= 0 }\n"
    manifest = {
        "revision": "1",
        "roots": ["policies/"],
        "members": ["data/data.json", "policies/allow.rego", "MANIFEST.json", ".signatures.json"],
    }
    files = {"data/data.json": data, "policies/allow.rego": policy}
    members = member_bytes(files, manifest["members"])
    cr = scoped_root(members, "policies/")
    sigs = [
        {
            "key_id": "beta",
            "scope": "policies/",
            "chain_root": cr,
            "signature": sign("policies/", cr, "beta"),
        }
    ]
    write_bundle("revoked-signer", manifest, files, sigs)



def trap_path_escape() -> None:
    """Manifest member ../../etc/passwd must be rejected during import-preview."""
    policy = (
        "package policy\n\n"
        "default allow = false\n\n"
        "allow { data.foo >= 0 }\n"
    )
    manifest = {
        "revision": "1",
        "roots": ["policies/"],
        "members": [
            "../../etc/passwd",
            "policies/allow.rego",
            "MANIFEST.json",
            ".signatures.json",
        ],
    }
    files = {"policies/allow.rego": policy}
    members = member_bytes(files, ["policies/allow.rego"])
    cr = scoped_root(members, "policies/")
    sigs = [
        {
            "key_id": "alpha",
            "scope": "policies/",
            "chain_root": cr,
            "signature": sign("policies/", cr, "alpha"),
        }
    ]
    write_bundle("path-escape", manifest, files, sigs)


def trap_bad_scope() -> None:
    data = '{"foo": 2}\n'
    policy = "package policy\n\ndefault allow = false\n\nallow { data.foo >= 0 }\n"
    manifest = {
        "revision": "1",
        "roots": ["data/"],
        "members": ["data/data.json", "policies/allow.rego", "MANIFEST.json", ".signatures.json"],
    }
    files = {"data/data.json": data, "policies/allow.rego": policy}
    members = member_bytes(files, manifest["members"])
    real = scoped_root(members, "data/")
    sigs = [
        {
            "key_id": "alpha",
            "scope": "data/",
            "chain_root": "00" * 32,
            "signature": sign("data/", real, "alpha"),
        }
    ]
    write_bundle("bad-scope-chain", manifest, files, sigs)


def trust_files() -> None:
    TRUST.mkdir(parents=True, exist_ok=True)
    (TRUST / "keys.json").write_text(json.dumps({"keys": KEYS}, indent=2) + "\n", encoding="utf-8")
    revoked = {"revoked": [{"key_id": "beta", "fingerprint": "fp:beta"}]}
    (TRUST / "revoked-keys.json").write_text(json.dumps(revoked, indent=2) + "\n", encoding="utf-8")
    for bundle in BUNDLES.iterdir():
        if not bundle.is_dir():
            continue
        tdir = bundle / "trust"
        tdir.mkdir(exist_ok=True)
        (tdir / "revoked-keys.json").write_text(
            (TRUST / "revoked-keys.json").read_text(encoding="utf-8"), encoding="utf-8"
        )


def seeds_json() -> None:
    (ROOT / "fixtures" / "seeds.json").write_text(
        json.dumps(["3", "7", "11", "19"], indent=2) + "\n", encoding="utf-8"
    )


def tb3_hidden_ledger_trap() -> None:
    """Hidden bundle: manifest order differs from lex order for data/ scope chain."""
    data = '{"foo": 880}\n'
    data_z = '{"meta": "z"}\n'
    data_a = '{"meta": "a"}\n'
    policy = "package policy\n\ndefault allow = false\n\nallow { data.foo >= input.threshold }\n"
    manifest = {
        "revision": "1",
        "roots": ["policies/", "data/"],
        "members": [
            "policies/allow.rego",
            "data/data.json",
            "data/z-extra.json",
            "data/a-extra.json",
            "MANIFEST.json",
            ".signatures.json",
        ],
    }
    files = {
        "data/data.json": data,
        "data/z-extra.json": data_z,
        "data/a-extra.json": data_a,
        "policies/allow.rego": policy,
    }
    members = member_bytes(files, manifest["members"])
    sigs = [
        {
            "key_id": "alpha",
            "scope": "data/",
            "chain_root": scoped_root(members, "data/"),
            "signature": sign("data/", scoped_root(members, "data/"), "alpha"),
        }
    ]
    out = Path("/opt/verifier-fixtures/tb3-bundles/ledger-trap")
    out.mkdir(parents=True, exist_ok=True)
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    for rel, content in files.items():
        path = out / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    sig = {"signatures": sigs}
    (out / ".signatures.json").write_text(json.dumps(sig, indent=2) + "\n", encoding="utf-8")
    (out / "input").mkdir(exist_ok=True)
    (out / "input/default.json").write_text('{"threshold": "__THRESHOLD__"}\n', encoding="utf-8")
    tdir = out / "trust"
    tdir.mkdir(exist_ok=True)
    (tdir / "revoked-keys.json").write_text(
        (TRUST / "revoked-keys.json").read_text(encoding="utf-8"), encoding="utf-8"
    )


def main() -> None:
    BUNDLES.mkdir(parents=True, exist_ok=True)
    good_allow_basic()
    good_deny_edge()
    good_multi_scope()
    path_normalize()
    trap_tampered()
    trap_revoked()
    trap_path_escape()
    trap_bad_scope()
    trust_files()
    seeds_json()
    tb3_hidden_ledger_trap()
    print(f"Generated bundles under {BUNDLES}")


if __name__ == "__main__":
    main()
