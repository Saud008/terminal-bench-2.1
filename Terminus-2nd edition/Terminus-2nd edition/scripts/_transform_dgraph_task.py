#!/usr/bin/env python3
"""Transform copied clickhouse task into dgraph-mutation-triple-blank-node-normalization-export."""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TASK = REPO / "tasks" / "dgraph-mutation-triple-blank-node-normalization-export"
ENV = TASK / "environment"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def rename_binary_content(root: Path) -> None:
    for p in root.rglob("*"):
        if p.is_dir() or p.suffix in {".zip", ".o"}:
            continue
        try:
            data = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        orig = data
        reps = [
            ("partwatermark", "dgraphguard"),
            ("partwatermark-seed-17", "dgraphguard-seed-23"),
            ("PartWatermark", "DgraphGuard"),
            ("part_stream_reader", "rdf_mutation_reader"),
            ("watermark_snapshot", "quad_snapshot"),
            ("tombstone_ledger_export", "predicate_ledger_export"),
            ("part-ledger.json", "predicate-ledger.json"),
            ("watermark-snapshot.json", "quad-snapshot.json"),
            ("fixtures/parts", "fixtures/mutations"),
            ("verifier-fixtures/parts", "verifier-fixtures/mutations"),
            ("verifier-broken-partwatermark-src", "verifier-broken-dgraphguard-src"),
            ("PWM_", "DGW_"),
            ("part_insertion_seq", "mutation_seq"),
            ("part_uuid", "mutation_uuid"),
            ("primary_key", "subject"),
            ("partition_id", "partition_key"),
            ("database", "graph"),
            ("table", "namespace"),
            ("max_part_version", "max_mutation_version"),
            ("watermark_digest", "snapshot_digest"),
            ("replacing-tree-coalesce", "blank-node-coalesce"),
            ("staging-watermark-schema", "staging-quad-schema"),
            ("part-uuid-tiebreak", "blank-node-canonical"),
            ("export-ledger-schema", "predicate-ledger-schema"),
            ("clickhouse-replacing-tree-part-watermark-export", "dgraph-mutation-triple-blank-node-normalization-export"),
            ("clickhouse", "dgraph"),
            ("ReplacingMergeTree", "Dgraph mutation"),
            ("part rows", "mutation triples"),
            ("PartRow", "QuadRow"),
            ("Part row", "Quad row"),
            ("parts file", "mutations file"),
            ("--parts", "--mutations"),
            ("read_parts_jsonl", "read_mutations_jsonl"),
            ("ingest_parts_to_snapshot", "replay_mutations_to_snapshot"),
            ("coalesce_parts_stream", "coalesce_mutations_stream"),
            ("reference_partwatermark", "reference_dgraphguard"),
            ("ingest_parts", "replay_mutations"),
            ("wrap_merge", "type_resolver"),
            ("merge_tree/compat", "schema/legacy"),
            ("wrap_merge.cpp", "type_resolver.cpp"),
        ]
        for a, b in reps:
            data = data.replace(a, b)
        if data != orig:
            p.write_text(data, encoding="utf-8")


def patch_common_hpp() -> None:
    p = ENV / "src" / "common.hpp"
    text = p.read_text(encoding="utf-8")
    if "predicate" not in text:
        text = text.replace(
            "    char subject[DGW_MAX_FIELD];\n    char mutation_uuid[DGW_MAX_FIELD];",
            "    char subject[DGW_MAX_FIELD];\n    char predicate[DGW_MAX_FIELD];\n"
            "    char object_value[DGW_MAX_FIELD];\n    char object_lang[DGW_MAX_FIELD];\n"
            "    char object_dtype[DGW_MAX_FIELD];\n    char mutation_uuid[DGW_MAX_FIELD];",
        )
        text = text.replace(
            "int compare_rows(const QuadRow *a, const QuadRow *b);",
            "int compare_rows(const QuadRow *a, const QuadRow *b);\n"
            "int blank_node_id(const char *subject);\n"
            "int literal_beats(const QuadRow *candidate, const QuadRow *incumbent);",
        )
        p.write_text(text, encoding="utf-8")


def patch_util_cpp() -> None:
    p = ENV / "src" / "util.cpp"
    text = p.read_text(encoding="utf-8")
    if "blank_node_id" not in text:
        insert = r'''
int blank_node_id(const char *subject) {
    if (subject[0] != '_' || subject[1] != ':' || subject[2] != 'b') return -1;
    return (int)strtol(subject + 3, NULL, 10);
}

int literal_beats(const QuadRow *candidate, const QuadRow *incumbent) {
    int c_has = incumbent->object_dtype[0] != '\0';
    int n_has = candidate->object_dtype[0] != '\0';
    if (n_has != c_has) return n_has > c_has ? 1 : 0;
    int dt = strcmp(candidate->object_dtype, incumbent->object_dtype);
    if (dt) return dt > 0 ? 1 : 0;
    return 0;
}

'''
        text = text.replace("int compare_rows", insert + "int compare_rows")
        text = text.replace(
            "    return strcmp(a->subject, b->subject);",
            "    int c = strcmp(a->subject, b->subject);\n    if (c) return c;\n    return strcmp(a->predicate, b->predicate);",
        )
        text = text.replace(
            """int row_beats(const QuadRow *candidate, const QuadRow *incumbent) {
    if (candidate->version != incumbent->version)
        return candidate->version > incumbent->version ? 1 : 0;
    return strcmp(candidate->mutation_uuid, incumbent->mutation_uuid) > 0 ? 1 : 0;
}""",
            """int row_beats(const QuadRow *candidate, const QuadRow *incumbent) {
    if (candidate->version != incumbent->version)
        return candidate->version > incumbent->version ? 1 : 0;
    int cb = blank_node_id(candidate->subject);
    int ib = blank_node_id(incumbent->subject);
    if (cb >= 0 && ib >= 0) return cb > ib ? 1 : 0;
    if (literal_beats(candidate, incumbent)) return 1;
    if (literal_beats(incumbent, candidate)) return 0;
    return strcmp(candidate->mutation_uuid, incumbent->mutation_uuid) > 0 ? 1 : 0;
}""",
        )
        text = text.replace(
            "        if (!strcmp(out_rows[j].graph, in_rows[i].graph) &&\n"
            "                !strcmp(out_rows[j].namespace, in_rows[i].namespace) &&\n"
            "                !strcmp(out_rows[j].partition_key, in_rows[i].partition_key) &&\n"
            "                !strcmp(out_rows[j].subject, in_rows[i].subject)) {",
            "        if (!strcmp(out_rows[j].graph, in_rows[i].graph) &&\n"
            "                !strcmp(out_rows[j].namespace, in_rows[i].namespace) &&\n"
            "                !strcmp(out_rows[j].partition_key, in_rows[i].partition_key) &&\n"
            "                !strcmp(out_rows[j].subject, in_rows[i].subject) &&\n"
            "                !strcmp(out_rows[j].predicate, in_rows[i].predicate)) {",
        )
        digest_old = (
            '        n += (size_t)snprintf(buf + n, sizeof(buf) - n, "%s|%s|%s|%s|%s|%lld|%lld|%d", r->graph,\n'
            '                              r->namespace, r->partition_key, r->subject, r->mutation_uuid,\n'
            '                              (long long)r->version, (long long)r->mutation_seq, r->is_deleted);'
        )
        digest_new = (
            '        n += (size_t)snprintf(buf + n, sizeof(buf) - n, "%s|%s|%s|%s|%s|%s|%lld|%lld|%d|%s|%s|%s", r->graph,\n'
            '                              r->namespace, r->partition_key, r->subject, r->predicate, r->mutation_uuid,\n'
            '                              (long long)r->version, (long long)r->mutation_seq, r->is_deleted,\n'
            '                              r->object_value, r->object_lang, r->object_dtype);'
        )
        text = text.replace(digest_old, digest_new)
        p.write_text(text, encoding="utf-8")


def patch_ingest_broken() -> None:
    p = ENV / "src" / "ingest" / "rdf_mutation_reader.cpp"
    if not p.exists():
        p = ENV / "src" / "ingest" / "part_stream_reader.cpp"
    text = p.read_text(encoding="utf-8")
    text = text.replace("part_stream_reader", "rdf_mutation_reader")
    text = text.replace("read_parts_jsonl", "read_mutations_jsonl")
    text = text.replace("coalesce_parts_stream", "coalesce_mutations_stream")
    text = text.replace(
        """static int row_wins_broken(const QuadRow *candidate, const QuadRow *incumbent) {
    if (candidate->mutation_seq != incumbent->mutation_seq)
        return candidate->mutation_seq > incumbent->mutation_seq ? 1 : 0;
    return strcmp(candidate->mutation_uuid, incumbent->mutation_uuid) > 0 ? 1 : 0;
}""",
        """static int row_wins_broken(const QuadRow *candidate, const QuadRow *incumbent) {
    if (candidate->mutation_seq != incumbent->mutation_seq)
        return candidate->mutation_seq > incumbent->mutation_seq ? 1 : 0;
    return strcmp(candidate->mutation_uuid, incumbent->mutation_uuid) > 0 ? 1 : 0;
}""",
    )
    # add predicate + object fields to json parse
    if '"predicate"' not in text:
        text = text.replace(
            '        if (extract_json_string(line, "subject", r.subject, sizeof(r.subject)) != 0) {',
            '        if (extract_json_string(line, "subject", r.subject, sizeof(r.subject)) != 0) {\n'
            "            fclose(f);\n            return -1;\n        }\n"
            '        if (extract_json_string(line, "predicate", r.predicate, sizeof(r.predicate)) != 0) {',
        )
        text = text.replace(
            '        if (extract_json_int64(line, "mutation_seq", &r.mutation_seq) != 0) {',
            '        if (extract_json_string(line, "object_value", r.object_value, sizeof(r.object_value)) != 0) {\n'
            "            fclose(f);\n            return -1;\n        }\n"
            '        if (extract_json_string(line, "object_lang", r.object_lang, sizeof(r.object_lang)) != 0) {\n'
            "            fclose(f);\n            return -1;\n        }\n"
            '        if (extract_json_string(line, "object_dtype", r.object_dtype, sizeof(r.object_dtype)) != 0) {\n'
            "            fclose(f);\n            return -1;\n        }\n"
            '        if (extract_json_int64(line, "mutation_seq", &r.mutation_seq) != 0) {',
        )
    p.write_text(text, encoding="utf-8")
    if p.name != "rdf_mutation_reader.cpp":
        dest = p.parent / "rdf_mutation_reader.cpp"
        dest.write_text(text, encoding="utf-8")
        p.unlink(missing_ok=True)


def patch_export_broken() -> None:
    for name in ("predicate_ledger_export.cpp", "tombstone_ledger_export.cpp"):
        p = ENV / "src" / "export" / name
        if p.exists():
            text = p.read_text(encoding="utf-8")
            text = text.replace("tombstone_ledger_export", "predicate_ledger_export")
            text = text.replace(
                '    snprintf(buf, sizeof(buf), "%s|%s|%lld", row->subject, row->mutation_uuid, (long long)row->version);',
                '    snprintf(buf, sizeof(buf), "%s|%s|%lld", row->subject, row->mutation_uuid, (long long)row->version);',
            )
            if "object_lang" not in text:
                text = text.replace(
                    '    snprintf(buf, sizeof(buf), "%s|%s|%lld", row->subject, row->mutation_uuid, (long long)row->version);',
                    '    snprintf(buf, sizeof(buf), "%s|%s|%lld|%d|%s|%s|%s", row->subject, row->predicate, (long long)row->version, row->is_deleted, row->object_value, row->object_lang, row->object_dtype);',
                )
            p.write_text(text, encoding="utf-8")
            if name != "predicate_ledger_export.cpp":
                (ENV / "src" / "export" / "predicate_ledger_export.cpp").write_text(text, encoding="utf-8")
                p.unlink(missing_ok=True)
            break


def patch_staging() -> None:
    for name in ("quad_snapshot.cpp", "watermark_snapshot.cpp"):
        p = ENV / "src" / "staging" / name
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        text = text.replace("watermark_snapshot", "quad_snapshot")
        text = text.replace("ingest_parts_to_snapshot", "replay_mutations_to_snapshot")
        text = text.replace("read_parts_jsonl", "read_mutations_jsonl")
        text = text.replace("coalesce_parts_stream", "coalesce_mutations_stream")
        text = text.replace("snapshot_recompute_digest", "snapshot_recompute_digest")
        dest = ENV / "src" / "staging" / "quad_snapshot.cpp"
        dest.write_text(text, encoding="utf-8")
        if name != "quad_snapshot.cpp":
            p.unlink(missing_ok=True)
        break


def patch_makefile() -> None:
    mf = ENV / "Makefile"
    text = mf.read_text(encoding="utf-8")
    text = text.replace("partwatermark", "dgraphguard")
    text = text.replace("part_stream_reader.cpp", "ingest/rdf_mutation_reader.cpp")
    text = text.replace("watermark_snapshot.cpp", "staging/quad_snapshot.cpp")
    text = text.replace("tombstone_ledger_export.cpp", "export/predicate_ledger_export.cpp")
    text = text.replace("wrap_merge.cpp", "schema/legacy/type_resolver.cpp")
    mf.write_text(text, encoding="utf-8")


def patch_main() -> None:
    main = ENV / "src" / "main.cpp"
    text = main.read_text(encoding="utf-8")
    text = text.replace("ingest", "replay")
    text = text.replace("--parts", "--mutations")
    text = text.replace("ingest_parts_to_snapshot", "replay_mutations_to_snapshot")
    main.write_text(text, encoding="utf-8")


def patch_fixtures_py() -> None:
    bf = ENV / "tools" / "build_fixtures.py"
    text = bf.read_text(encoding="utf-8")
    text = text.replace("partwatermark", "dgraphguard")
    text = text.replace("parts", "mutations")
    text = text.replace("primary_key", "subject")
    text = text.replace("part_uuid", "mutation_uuid")
    text = text.replace("part_insertion_seq", "mutation_seq")
    text = text.replace("partition_id", "partition_key")
    text = text.replace("database", "graph")
    text = text.replace("table", "namespace")

    def row_sig(old: str) -> str:
        return old.replace(
            "def row(",
            "def row(\n    graph, namespace, partition_key, subject, predicate, object_value, object_lang, object_dtype, mutation_uuid, version, mutation_seq, is_deleted,\n):  # noqa",
        )

    text = re.sub(
        r"def row\([\s\S]*?\) -> dict:",
        """def row(
    graph: str,
    namespace: str,
    partition_key: str,
    subject: str,
    predicate: str,
    object_value: str,
    object_lang: str,
    object_dtype: str,
    mutation_uuid: str,
    version: int,
    mutation_seq: int,
    is_deleted: int,
) -> dict:""",
        text,
        count=1,
    )
    text = re.sub(
        r'return \{[\s\S]*?"is_deleted": is_deleted,\s*\}',
        """return {
        "graph": graph,
        "namespace": namespace,
        "partition_key": partition_key,
        "subject": subject,
        "predicate": predicate,
        "object_value": object_value,
        "object_lang": object_lang,
        "object_dtype": object_dtype,
        "mutation_uuid": mutation_uuid,
        "version": version,
        "mutation_seq": mutation_seq,
        "is_deleted": is_deleted,
    }""",
        text,
        count=1,
    )
    # rewrite fixture bodies
    fixtures = '''
    write_jsonl(
        out / "basic_merge.jsonl",
        [
            row("prod", "default", "pk0", "user:1", "name", "Ann", "", "", "mut-111", 1, 10, 0),
            row("prod", "default", "pk0", "user:1", "name", "Anna", "", "", "mut-222", 2, 5, 0),
            row("prod", "default", "pk0", "user:2", "name", "Bob", "", "", "mut-333", 1, 11, 0),
        ],
    )

    write_jsonl(
        out / "blank_node_tie.jsonl",
        [
            row("graph-a", "ns1", "shard-0", "_:b2", "knows", "x", "", "", "mut-zulu", 5, 50, 0),
            row("graph-a", "ns1", "shard-0", "_:b10", "knows", "y", "", "", "mut-alpha", 5, 100, 0),
        ],
    )

    write_jsonl(
        out / "typed_literal.jsonl",
        [
            row("crm", "contacts", "east", "node:42", "age", "42", "", "", "del-001", 3, 20, 1),
            row("crm", "contacts", "east", "node:42", "age", "42", "", "xsd:int", "live-002", 4, 21, 0),
        ],
    )

    write_jsonl(
        out / "empty_batch.jsonl",
        [],
    )

    write_jsonl(
        out / "resume_seed.jsonl",
        [
            row("telemetry", "metrics", "shard-1", "cpu-0", "load", "0.9", "", "", "mut-a", 2, 1, 0),
            row("telemetry", "metrics", "shard-1", "cpu-1", "load", "0.5", "", "", "mut-b", 1, 2, 0),
        ],
    )
'''
    text = re.sub(
        r"write_jsonl\(\s*out / \"basic_merge\.jsonl\"[\s\S]*?write_jsonl\(\s*out / \"resume_seed\.jsonl\"[\s\S]*?\),\s*\)",
        fixtures.strip(),
        text,
        count=1,
    )
    text = text.replace("/app/fixtures/parts", "/app/fixtures/mutations")
    bf.write_text(text, encoding="utf-8")

    hf = ENV / "tools" / "build_hidden_fixtures.py"
    ht = hf.read_text(encoding="utf-8")
    ht = ht.replace("parts", "mutations")
    ht = ht.replace("/opt/verifier-fixtures/parts", "/opt/verifier-fixtures/mutations")
    hidden = '''
    write_jsonl(
        out / "hidden_blank_node_tie.jsonl",
        [
            row("hidden", "facts", "tb3-a", "_:b3", "rel", "a", "", "", "uuid-mike", 7, 200, 0),
            row("hidden", "facts", "tb3-a", "_:b12", "rel", "b", "", "", "uuid-oscar", 7, 80, 0),
            row("hidden", "facts", "tb3-a", "solid:1", "rel", "c", "", "", "uuid-papa", 6, 90, 0),
        ],
    )

    write_jsonl(
        out / "hidden_literal_lang_digest.jsonl",
        [
            row("hidden", "ledger", "tb3-b", "acct-7", "title", "Hi", "en", "", "aaa-tomb", 4, 99, 1),
            row("hidden", "ledger", "tb3-b", "acct-7", "title", "Hi", "de", "", "zzz-live", 4, 1, 0),
            row("hidden", "ledger", "tb3-b", "acct-8", "title", "Only", "", "", "only-z", 2, 12, 0),
        ],
    )

    write_jsonl(
        out / "hidden_resume_batch1.jsonl",
        [
            row("hidden", "stream", "s0", "evt-1", "val", "3", "", "", "p-100", 3, 1, 0),
            row("hidden", "stream", "s0", "evt-2", "val", "2", "", "", "p-101", 2, 2, 0),
        ],
    )

    write_jsonl(
        out / "hidden_resume_batch2.jsonl",
        [
            row("hidden", "stream", "s0", "evt-1", "val", "4", "", "", "p-102", 3, 3, 0),
            row("hidden", "stream", "s0", "evt-3", "val", "1", "", "", "p-103", 1, 4, 0),
        ],
    )
'''
    ht = re.sub(
        r"write_jsonl\([\s\S]*$",
        hidden.strip() + "\n\n    return 0\n\n\nif __name__ == \"__main__\":\n    raise SystemExit(main())\n",
        ht,
        count=1,
    )
    hf.write_text(text, encoding="utf-8")


def patch_reference() -> None:
    ref = TASK / "tests" / "reference_dgraphguard.py"
    if not ref.exists():
        ref = TASK / "tests" / "reference_partwatermark.py"
    text = REFERENCE if 'REFERENCE' in globals() else ref.read_text(encoding="utf-8")
    # use embedded reference from bootstrap
    ref_path = TASK / "tests" / "reference_dgraphguard.py"
    ref_path.write_text(Path(__file__).with_name("_ref_dgraph.py").read_text(encoding="utf-8") if Path(__file__).with_name("_ref_dgraph.py").exists() else "", encoding="utf-8")


def patch_task_toml() -> None:
    toml = TASK / "task.toml"
    text = toml.read_text(encoding="utf-8")
    text = re.sub(r'tags = \[.*?\]', 'tags = ["dgraph", "rdf", "blank-node", "mutation", "jsonl", "cpp-cli"]', text)
    text = text.replace('languages = ["cpp", "bash"]', 'languages = ["cpp", "bash"]')
    toml.write_text(text, encoding="utf-8")


def patch_instruction() -> None:
    ins = TASK / "instruction.md"
    ins.write_text(
        """Implement the dgraphguard Dgraph mutation triple blank-node normalization CLI at /usr/local/bin/dgraphguard and complete the C++ sources under /app/src/. The tool replays JSONL mutation triple streams from /app/fixtures/mutations/, persists a staging quad snapshot at /app/state/quad-snapshot.json, and publishes a predicate ledger export to /app/output/predicate-ledger.json.

Behavioral contracts live in /app/docs/blank-node-coalesce.md, /app/docs/staging-quad-schema.md, /app/docs/blank-node-canonical.md, /app/docs/predicate-ledger-schema.md, /app/docs/cli-surface.md, /app/docs/fixture-catalog.md, and /app/docs/module-api.md. Bundled fixtures are under /app/fixtures/mutations/. When TB3_FIXTURES_DIR points at an absolute directory under /opt/verifier-fixtures/mutations/, the same replay-staging-publish pipeline must handle those hidden fixtures with matching snapshot digests and ledger checksums.

replay must reject missing or corrupt JSONL with exit 1. Missing required flags exit 2. publish must read only the staging snapshot and must not reopen mutation fixture files. Rebuild with make -C /app install after source edits. Do not run apt-get, pip install, or other network installs.

Do not edit /app/docs/, /app/fixtures/, or /app/tools/.
""",
        encoding="utf-8",
    )


def rename_patches() -> None:
    pmap = {
        "part_stream_reader.cpp": "rdf_mutation_reader.cpp",
        "watermark_snapshot.cpp": "quad_snapshot.cpp",
        "tombstone_ledger_export.cpp": "predicate_ledger_export.cpp",
        "wrap_merge.cpp": "type_resolver.cpp",
    }
    for folder in (TASK / "tests" / "patches", TASK / "solution" / "patches", TASK / "tests" / "broken_src"):
        if not folder.exists():
            continue
        for old, new in pmap.items():
            for p in list(folder.rglob(old)):
                p.rename(p.with_name(new))
        # flatten broken_src paths like clickhouse
        for sub in ("ingest", "staging", "export", "state", "schema/legacy", "merge_tree/compat"):
            d = folder / sub
            if d.is_dir():
                for f in d.glob("*.cpp"):
                    dest = folder / f.name if sub == "ingest" else folder / Path(sub).name / f.name
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if not dest.exists():
                        shutil.copy2(f, dest)


def main() -> None:
    rename_binary_content(TASK)
    patch_common_hpp()
    patch_util_cpp()
    patch_ingest_broken()
    patch_export_broken()
    patch_staging()
    patch_makefile()
    patch_main()
    patch_fixtures_py()
    patch_instruction()
    patch_task_toml()
    rename_patches()
    # reference
    ref_src = REPO / "scripts" / "_ref_dgraph.py"
    if ref_src.exists():
        shutil.copy2(ref_src, TASK / "tests" / "reference_dgraphguard.py")
    # rename test file imports
    to = TASK / "tests" / "test_outputs.py"
    if to.exists():
        t = to.read_text(encoding="utf-8")
        t = t.replace("part_stream_reader", "rdf_mutation_reader")
        t = t.replace("watermark_snapshot", "quad_snapshot")
        t = t.replace("tombstone_ledger_export", "predicate_ledger_export")
        t = t.replace("version_tie_uuid", "blank_node_tie")
        t = t.replace("tombstone_live", "typed_literal")
        t = t.replace("uuid-zulu", "_:b10")
        t = t.replace("uuid-alpha", "_:b2")
        t = t.replace("live-002", "live-002")
        t = t.replace("TestPartWatermark", "TestDgraphGuard")
        t = t.replace("TestHiddenParts", "TestHiddenMutations")
        t = t.replace("hidden_version_tie", "hidden_blank_node_tie")
        t = t.replace("hidden_tombstone_resurrection", "hidden_literal_lang_digest")
        t = t.replace("uuid-oscar", "_:b12")
        t = t.replace("k1", "k1")
        t = t.replace("zzz-live", "zzz-live")
        t = t.replace("_ingest(", "_replay(")
        t = t.replace('["ingest",', '["replay",')
        t = t.replace('def _ingest', 'def _replay')
        t = t.replace("FIXTURES / \"parts\"", "FIXTURES / \"mutations\"")
        t = t.replace("/opt/verifier-fixtures/parts", "/opt/verifier-fixtures/mutations")
        t = t.replace("ingest_parts", "replay_mutations")
        t = t.replace("part_uuid", "mutation_uuid")
        t = t.replace("primary_key", "subject")
        to.write_text(t, encoding="utf-8")
    # solution solve
    sol = TASK / "solution" / "solve.sh"
    if sol.exists():
        s = sol.read_text(encoding="utf-8")
        s = s.replace("part_stream_reader.cpp", "rdf_mutation_reader.cpp")
        s = s.replace("watermark_snapshot.cpp", "quad_snapshot.cpp")
        s = s.replace("tombstone_ledger_export.cpp", "predicate_ledger_export.cpp")
        s = s.replace("basic_merge.jsonl", "basic_merge.jsonl")
        s = s.replace("ingest", "replay")
        s = s.replace("--parts", "--mutations")
        sol.write_text(s, encoding="utf-8")
    # test.sh
    ts = TASK / "tests" / "test.sh"
    if ts.exists():
        x = ts.read_text(encoding="utf-8")
        x = x.replace("partwatermark-seed-17", "dgraphguard-seed-23")
        x = x.replace("verifier-fixtures/parts", "verifier-fixtures/mutations")
        ts.write_text(x, encoding="utf-8")
    # Dockerfile paths
    df = ENV / "Dockerfile"
    d = df.read_text(encoding="utf-8")
    d = d.replace("fixtures/parts", "fixtures/mutations")
    d = d.replace("verifier-fixtures/parts", "verifier-fixtures/mutations")
    d = d.replace("verifier-broken-partwatermark-src", "verifier-broken-dgraphguard-src")
    d = d.replace("build_fixtures.py /app/fixtures/parts", "build_fixtures.py /app/fixtures/mutations")
    df.write_text(d, encoding="utf-8")
    print("transform complete")


if __name__ == "__main__":
    main()
