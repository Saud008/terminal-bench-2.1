"""Verifier: LDAP changelog shadow-sync ingest and sealed export ops."""

from __future__ import annotations

import hashlib
import json
import subprocess
import uuid
from pathlib import Path

from harness import (
    BIN,
    FIXTURES,
    export_shadow,
    ingest_ldif,
    read_json,
    read_staging,
    reset_state,
)
from reference_ldif import (
    build_audit_doc,
    build_case_collision_ldif,
    build_shadow_doc,
    ingest_file_reference,
    ingest_reference,
    max_applied_usn,
    normalize_dn,
    parse_ldif_file,
    rewrite_base_dn,
)

APP = Path("/app")
PROTECTED_SHA256: dict[str, str] = {
    "docs/changelog-ldif.md": "ad753818604d39f7c45afb12ef18b432a351d1980faca9dacab4ab80e251b93a",
    "docs/cli.md": "a7086c4074d1b520524fac8512e26ad3a99c20a252745b3dc6a0ba4879768789",
    "docs/dn-normalization.md": "677056346a02af7a796504ad96e8c8bd77c556a1e0a1ede1b134b84a4d15c1f6",
    "docs/export-format.md": "a7140638818f40f48202c860090bc3593bcdb2f6d2d6d8d4d46b90a3dc3ac378",
    "docs/replay-idempotency.md": "e0b7168f8ea09ef5592e05cd0866cb9960902f667febb517b8a7189042316760",
    "docs/staging-contract.md": "64c0e487c993744483e4f316db549b0d85a38387f5da3782a681f6cdf7adc659",
    "fixtures/alpha_changelog.ldif": "22b0f42a690f297fe140df192409c56239de8d0ec02511d84b674527b023fc31",
    "fixtures/beta_changelog.ldif": "f2085db6e0b059035b9e1f6f05ad323e4e08968c084313056abd73aa8f080dd8",
    "fixtures/README.md": "0dcc5bdc83e85470d5fb29008c32ac69be3f07ae0b5c14c7fb5579f85acf841a",
}

TB3_DN_ESCAPE = Path("/opt/verifier-fixtures/dn-escape-trap.ldif")
TB3_EXPORT_TRAP = Path("/opt/verifier-fixtures/export-count-trap.ldif")
TB3_CN_ORDER = Path("/opt/verifier-fixtures/changenumber-order-trap.ldif")
TB3_ATTR_CASE = Path("/opt/verifier-fixtures/attr-case-trap.ldif")
TB3_MAX_USN = Path("/opt/verifier-fixtures/max-usn-delete-trap.ldif")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestProtectedInputs:
    """Bundled contract docs and fixtures must remain unchanged."""

    def test_docs_and_fixtures_unmodified(self) -> None:
        """Agent must not edit /app/docs/ or /app/fixtures/."""
        for rel, expected in PROTECTED_SHA256.items():
            assert _sha256(APP / rel) == expected, rel


class TestIngestOps:
    """Changelog ingest into staging and SQLite shadow."""

    def test_binary_exists(self) -> None:
        """Binary /app/bin/shadow-sync must exist after rebuild."""
        assert BIN.is_file(), "missing /app/bin/shadow-sync"

    def test_ingest_writes_staging_and_db(self) -> None:
        """Ingest must persist /app/state/changelog-staging.jsonl and /app/state/shadow.db."""
        reset_state()
        ingest_ldif(FIXTURES / "alpha_changelog.ldif")
        assert Path("/app/state/changelog-staging.jsonl").is_file()
        assert Path("/app/state/shadow.db").is_file()
        assert Path("/app/state/last-ingest-stats.json").is_file()

    def test_alpha_mail_modify_order(self) -> None:
        """Add-then-delete mail in one modify must leave Alice without mail."""
        reset_state()
        path = FIXTURES / "alpha_changelog.ldif"
        ingest_ldif(path)
        ref_shadow, ref_staging, _ = ingest_file_reference(path)
        alice_dn = normalize_dn("cn=Alice,ou=People,dc=example,dc=com")
        assert ref_shadow[alice_dn].get("mail") is None
        rows = read_staging()
        assert len(rows) == len(ref_staging)
        alice_rows = [r for r in rows if r.get("attrs", {}).get("cn") == "Alice"]
        assert alice_rows, "expected Alice staging rows"
        assert alice_rows[-1]["attrs"].get("mail") is None
        assert alice_rows[-1]["attrs"].get("cn") == "Alice"

    def test_hidden_case_variant_dn_collision(self) -> None:
        """Case-only DN variants must merge to one shadow entry."""
        reset_state()
        suffix = f"hid{uuid.uuid4().hex[:10]}"
        ldif_text = build_case_collision_ldif(suffix)
        hidden = Path(f"/tmp/case_{suffix}.ldif")
        hidden.write_text(ldif_text, encoding="utf-8")
        ingest_ldif(hidden)
        norm = normalize_dn(f"CN=Case User,OU=People,dc={suffix},dc=local")
        rows = read_staging()
        assert len(rows) == 2
        final = rows[-1]
        assert final["normalized_dn"] == norm
        assert final["attrs"]["cn"] == "Case User"
        assert final["attrs"]["mail"] == "CASE@example.com"
        assert len({r["normalized_dn"] for r in rows}) == 1

    def test_usn_replay_idempotent_staging(self) -> None:
        """Re-ingesting the same changelog must not duplicate staging lines."""
        reset_state()
        path = FIXTURES / "alpha_changelog.ldif"
        ingest_ldif(path)
        first_count = len(read_staging())
        ingest_ldif(path)
        second_count = len(read_staging())
        assert second_count == first_count
        stats = json.loads(Path("/app/state/last-ingest-stats.json").read_text(encoding="utf-8"))
        assert stats["replay_noop"] == len(parse_ldif_file(path))
        assert stats["new_usns"] == 0

    def test_per_test_base_dn_suffix(self) -> None:
        """Hidden LDIF with rewritten base DN still normalizes attribute types only."""
        reset_state()
        suffix = f"t{uuid.uuid4().hex[:8]}"
        raw = rewrite_base_dn((FIXTURES / "alpha_changelog.ldif").read_text(encoding="utf-8"), suffix)
        hidden = Path(f"/tmp/alpha_{suffix}.ldif")
        hidden.write_text(raw, encoding="utf-8")
        ingest_ldif(hidden)
        _, ref_staging, _ = ingest_file_reference(hidden)
        rows = read_staging()
        assert len(rows) == len(ref_staging)
        bob_rows = [r for r in rows if r.get("attrs", {}).get("cn") == "Bob"]
        assert bob_rows
        assert "bob" in bob_rows[-1]["attrs"]["mail"].lower()

    def test_cli_ingest_invokes_subprocess(self) -> None:
        """shadow-sync ingest-ldif must run as a subprocess CLI."""
        reset_state()
        proc = subprocess.run(
            [str(BIN), "ingest-ldif", "--input", str(FIXTURES / "alpha_changelog.ldif")],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
        assert Path("/app/state/changelog-staging.jsonl").is_file()

    def test_tb3_dn_escape_normalization(self) -> None:
        """Escaped commas in /opt/verifier-fixtures/dn-escape-trap.ldif must not split the RDN."""
        reset_state()
        ingest_ldif(TB3_DN_ESCAPE)
        norm = normalize_dn(r"cn=Last\, First,ou=People,dc=tb3,dc=local")
        rows = read_staging()
        assert len(rows) == 1
        assert rows[0]["normalized_dn"] == norm
        assert rows[0]["attrs"]["cn"] == "Last, First"

    def test_first_ingest_stats_new_usn_count(self) -> None:
        """First alpha ingest must record four new USNs in last-ingest-stats.json."""
        reset_state()
        ingest_ldif(FIXTURES / "alpha_changelog.ldif")
        stats = json.loads(Path("/app/state/last-ingest-stats.json").read_text(encoding="utf-8"))
        assert stats["new_usns"] == 4
        assert stats["replay_noop"] == 0

    def test_staging_rows_sorted_by_change_number(self) -> None:
        """Staging JSONL must follow changelog changeNumber order."""
        reset_state()
        ingest_ldif(FIXTURES / "alpha_changelog.ldif")
        numbers = [row["change_number"] for row in read_staging()]
        assert numbers == sorted(numbers)

    def test_alice_description_preserved_after_mail_ops(self) -> None:
        """Mail replace/delete must not drop unrelated attributes on Alice."""
        reset_state()
        ingest_ldif(FIXTURES / "alpha_changelog.ldif")
        alice_dn = normalize_dn("cn=Alice,ou=People,dc=example,dc=com")
        rows = [r for r in read_staging() if r["normalized_dn"] == alice_dn]
        assert rows[-1]["attrs"].get("description") == "original"


class TestExportOps:
    """Export unique DN counts and replay-stable audit sequence."""

    def test_export_writes_shadow_and_audit_files(self) -> None:
        """Export must write /app/output/shadow.json and /app/output/shadow-audit.json."""
        reset_state()
        ingest_ldif(FIXTURES / "alpha_changelog.ldif")
        export_shadow()
        assert Path("/app/output/shadow.json").is_file()
        assert Path("/app/output/shadow-audit.json").is_file()

    def test_beta_unique_dn_counts(self) -> None:
        """Audit must count unique DNs, not staging lines."""
        reset_state()
        path = FIXTURES / "beta_changelog.ldif"
        ingest_ldif(path)
        shadow, staging, stats = ingest_file_reference(path)
        shadow_path, audit_path = export_shadow()
        shadow_doc = read_json(shadow_path)
        audit_doc = read_json(audit_path)
        assert len(shadow) == 2
        assert len(staging) == 4
        assert shadow_doc["entry_count"] == 2
        assert audit_doc["unique_dn_count"] == 2
        assert audit_doc["changelog_lines_applied"] == 4
        assert audit_doc["replay_stats"]["new_usns"] == stats.new_usns

    def test_decoy_merge_not_double_applied(self) -> None:
        """Carol title must remain Senior Engineer after export."""
        reset_state()
        ingest_ldif(FIXTURES / "beta_changelog.ldif")
        shadow_path, _ = export_shadow()
        doc = read_json(shadow_path)
        carol_dn = normalize_dn("cn=Carol,ou=Staff,dc=example,dc=com")
        carol = next(e for e in doc["entries"] if e["normalized_dn"] == carol_dn)
        assert carol["attrs"]["title"] == "Senior Engineer"
        assert carol["attrs"]["mail"] == "carol@example.com"

    def test_export_sequence_replay_stable(self) -> None:
        """Re-ingest with only known USNs must not bump export_sequence."""
        reset_state()
        path = FIXTURES / "beta_changelog.ldif"
        ingest_ldif(path)
        _, audit1 = export_shadow()
        seq1 = read_json(audit1)["export_sequence"]
        ingest_ldif(path)
        _, audit2 = export_shadow()
        audit2_doc = read_json(audit2)
        assert audit2_doc["export_sequence"] == seq1
        assert audit2_doc["replay_stats"]["replay_noop"] == 4
        assert audit2_doc["replay_stats"]["new_usns"] == 0

    def test_hidden_suffix_export_oracle(self) -> None:
        """Export matches reference for rewritten base DN fixture."""
        reset_state()
        suffix = f"ex{uuid.uuid4().hex[:8]}"
        raw = rewrite_base_dn((FIXTURES / "beta_changelog.ldif").read_text(encoding="utf-8"), suffix)
        hidden = Path(f"/tmp/beta_{suffix}.ldif")
        hidden.write_text(raw, encoding="utf-8")
        records = parse_ldif_file(hidden)
        ingest_ldif(hidden)
        shadow, staging, stats = ingest_reference(records)
        shadow_path, audit_path = export_shadow()
        got_shadow = read_json(shadow_path)
        got_audit = read_json(audit_path)
        usn_map = {}
        for rec in records:
            usn_map[normalize_dn(rec.dn)] = rec.usn_changed
        ref_shadow = build_shadow_doc(shadow, usn_map)
        ref_audit = build_audit_doc(
            shadow,
            len(staging),
            max_applied_usn(records),
            1,
            stats,
        )
        assert got_shadow["entry_count"] == ref_shadow["entry_count"]
        assert got_audit["unique_dn_count"] == ref_audit["unique_dn_count"]
        assert got_audit["max_usn"] == ref_audit["max_usn"]

    def test_first_export_sequence_is_one(self) -> None:
        """First export with new USNs sets export_sequence to 1."""
        reset_state()
        ingest_ldif(FIXTURES / "alpha_changelog.ldif")
        _, audit_path = export_shadow()
        audit = read_json(audit_path)
        assert audit["export_sequence"] == 1
        assert audit["replay_stats"]["new_usns"] == 4

    def test_cli_export_invokes_subprocess(self) -> None:
        """shadow-sync export must run as a subprocess CLI."""
        reset_state()
        ingest_ldif(FIXTURES / "alpha_changelog.ldif")
        proc = subprocess.run(
            [
                str(BIN),
                "export",
                "--db",
                "/app/state/shadow.db",
                "--shadow",
                "/app/output/shadow.json",
                "--audit",
                "/app/output/shadow-audit.json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
        assert Path("/app/output/shadow.json").is_file()

    def test_tb3_export_unique_dn_count_trap(self) -> None:
        """Export must count two live DNs for /opt/verifier-fixtures/export-count-trap.ldif."""
        reset_state()
        ingest_ldif(TB3_EXPORT_TRAP)
        shadow_path, audit_path = export_shadow()
        shadow_doc = read_json(shadow_path)
        audit_doc = read_json(audit_path)
        assert shadow_doc["entry_count"] == 2
        assert audit_doc["unique_dn_count"] == 2
        assert audit_doc["changelog_lines_applied"] == 5
        grace_dn = normalize_dn("cn=Grace,ou=Staff,dc=tb3,dc=local")
        assert any(e["normalized_dn"] == grace_dn for e in shadow_doc["entries"])

    def test_shadow_entries_sorted_by_normalized_dn(self) -> None:
        """Exported shadow.json entries must be sorted by normalized_dn."""
        reset_state()
        ingest_ldif(FIXTURES / "beta_changelog.ldif")
        shadow_path, _ = export_shadow()
        dns = [e["normalized_dn"] for e in read_json(shadow_path)["entries"]]
        assert dns == sorted(dns)

    def test_audit_max_usn_matches_changelog(self) -> None:
        """Audit max_usn must reflect the highest applied uSNChanged value."""
        reset_state()
        path = FIXTURES / "beta_changelog.ldif"
        records = parse_ldif_file(path)
        ingest_ldif(path)
        _, audit_path = export_shadow()
        expected = max(r.usn_changed for r in records)
        assert read_json(audit_path)["max_usn"] == expected

    def test_export_replay_stats_match_last_ingest(self) -> None:
        """Audit replay_stats must mirror /app/state/last-ingest-stats.json."""
        reset_state()
        ingest_ldif(FIXTURES / "beta_changelog.ldif")
        ingest_stats = read_json(Path("/app/state/last-ingest-stats.json"))
        _, audit_path = export_shadow()
        replay = read_json(audit_path)["replay_stats"]
        assert replay["new_usns"] == ingest_stats["new_usns"]
        assert replay["replay_noop"] == ingest_stats["replay_noop"]

    def test_staging_line_count_matches_audit(self) -> None:
        """changelog_lines_applied must equal staging JSONL row count after ingest."""
        reset_state()
        ingest_ldif(FIXTURES / "beta_changelog.ldif")
        _, audit_path = export_shadow()
        assert read_json(audit_path)["changelog_lines_applied"] == len(read_staging())

    def test_tb3_changenumber_file_order_trap(self) -> None:
        """Out-of-order changeNumber blocks must still apply ascending."""
        reset_state()
        ingest_ldif(TB3_CN_ORDER)
        ivy_dn = normalize_dn("cn=Ivy,ou=Staff,dc=tb3,dc=local")
        rows = read_staging()
        assert [r["change_number"] for r in rows] == [70, 71, 72]
        final = rows[-1]
        assert final["normalized_dn"] == ivy_dn
        assert final["attrs"]["title"] == "Director"
        assert final["attrs"]["mail"] == "ivy@example.com"
        shadow_path, _ = export_shadow()
        ivy = next(e for e in read_json(shadow_path)["entries"] if e["normalized_dn"] == ivy_dn)
        assert ivy["attrs"]["title"] == "Director"
        assert ivy["attrs"]["mail"] == "ivy@example.com"

    def test_tb3_attr_name_case_fold(self) -> None:
        """Mixed-case LDIF attribute names must store as lowercase keys."""
        reset_state()
        ingest_ldif(TB3_ATTR_CASE)
        jules_dn = normalize_dn("CN=Jules,OU=People,dc=tb3,dc=local")
        rows = [r for r in read_staging() if r["normalized_dn"] == jules_dn]
        assert rows
        assert "Mail" not in rows[0]["attrs"]
        assert rows[0]["attrs"]["mail"] == "Jules@Example.com"
        assert rows[-1]["attrs"]["title"] == "Senior Engineer"
        assert rows[-1]["modify_ops"][-1]["attr"] == "title"
        shadow_path, _ = export_shadow()
        jules = next(e for e in read_json(shadow_path)["entries"] if e["normalized_dn"] == jules_dn)
        assert set(jules["attrs"]) == {"objectclass", "cn", "mail", "title"}
        assert jules["attrs"]["title"] == "Senior Engineer"

    def test_tb3_max_usn_includes_deleted(self) -> None:
        """Audit max_usn must keep the deleted entry's applied USN."""
        reset_state()
        ingest_ldif(TB3_MAX_USN)
        shadow_path, audit_path = export_shadow()
        shadow_doc = read_json(shadow_path)
        audit_doc = read_json(audit_path)
        assert shadow_doc["entry_count"] == 1
        assert audit_doc["unique_dn_count"] == 1
        assert audit_doc["max_usn"] == 9002
        assert audit_doc["changelog_lines_applied"] == 3
