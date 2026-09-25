#!/usr/bin/env python3
"""Rebuild opa-bundle-signature-digest-chain-verifier task (NOP-hard + ruff-clean)."""
from __future__ import annotations

from pathlib import Path

TASK = Path(
    r"c:\Users\masau\Downloads\Terminus-2nd edition (1)\Terminus-2nd edition"
    r"\Terminus-2nd edition\tasks\opa-bundle-signature-digest-chain-verifier"
)
ENV = TASK / "environment"
SOL = TASK / "solution"
TESTS = TASK / "tests"
STUBS = TESTS / "stubs"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    print("wrote", path.relative_to(TASK), len(text))


def patch_gen_fixtures() -> None:
    gf_path = ENV / "tools" / "gen_fixtures.py"
    gf = gf_path.read_text(encoding="utf-8")
    gf = gf.replace(
        "opa-bundle-signature-digest-chain-verifier-repair",
        "opa-bundle-signature-digest-chain-verifier",
    )
    old_canon = '''def canonical(path: str) -> str:
    p = path.replace("\\\\", "/")
    if p.startswith("./"):
        p = p[2:]
'''
    # file uses single backslash in source
    old_canon = (
        "def canonical(path: str) -> str:\n"
        '    p = path.replace("\\\\", "/")\n'
        '    if p.startswith("./"):\n'
        "        p = p[2:]\n"
    )
    # Read actual bytes for the startswith block
    if 'if p.startswith("./"):' in gf:
        gf = gf.replace(
            '    p = path.replace("\\", "/")\n    if p.startswith("./"):\n        p = p[2:]\n',
            '    p = path.replace("\\", "/").removeprefix("./")\n',
        )
    trap = '''
def trap_path_escape() -> None:
    """Manifest member ../../etc/passwd must be rejected during import-preview."""
    policy = "package policy\\n\\ndefault allow = false\\n\\nallow { data.foo >= 0 }\\n"
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


'''
    # Fix escaped newlines in trap - use real newlines in policy string
    trap = '''
def trap_path_escape() -> None:
    """Manifest member ../../etc/passwd must be rejected during import-preview."""
    policy = (
        "package policy\\n\\n"
        "default allow = false\\n\\n"
        "allow { data.foo >= 0 }\\n"
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


'''
    # Actually write with proper Python string content
    trap = (
        "\ndef trap_path_escape() -> None:\n"
        '    """Manifest member ../../etc/passwd must be rejected during import-preview."""\n'
        "    policy = (\n"
        '        "package policy\\n\\n"\n'
        '        "default allow = false\\n\\n"\n'
        '        "allow { data.foo >= 0 }\\n"\n'
        "    )\n"
        "    manifest = {\n"
        '        "revision": "1",\n'
        '        "roots": ["policies/"],\n'
        '        "members": [\n'
        '            "../../etc/passwd",\n'
        '            "policies/allow.rego",\n'
        '            "MANIFEST.json",\n'
        '            ".signatures.json",\n'
        "        ],\n"
        "    }\n"
        '    files = {"policies/allow.rego": policy}\n'
        '    members = member_bytes(files, ["policies/allow.rego"])\n'
        '    cr = scoped_root(members, "policies/")\n'
        "    sigs = [\n"
        "        {\n"
        '            "key_id": "alpha",\n'
        '            "scope": "policies/",\n'
        '            "chain_root": cr,\n'
        '            "signature": sign("policies/", cr, "alpha"),\n'
        "        }\n"
        "    ]\n"
        '    write_bundle("path-escape", manifest, files, sigs)\n\n\n'
    )
    if "def trap_path_escape" not in gf:
        gf = gf.replace("def trap_bad_scope()", trap + "def trap_bad_scope()")
    if "trap_path_escape()" not in gf.split("def main")[-1]:
        gf = gf.replace(
            "trap_revoked()\n    trap_bad_scope()",
            "trap_revoked()\n    trap_path_escape()\n    trap_bad_scope()",
        )
    gf_path.write_text(gf, encoding="utf-8", newline="\n")
    print("patched gen_fixtures", "path-escape" in gf)


def write_broken_sources() -> None:
    """Intentional bugs that compile but fail contract acceptance."""
    # preview_ledger: manifest order (not lex) — compiles
    write(
        ENV / "internal/bundle/preview_ledger.go",
        r'''package bundle

import (
	"encoding/json"
	"os"
	"path/filepath"
)

type PreviewEntry struct {
	Raw       string `json:"raw"`
	Canonical string `json:"canonical"`
}

type PreviewLedger struct {
	Bundle  string         `json:"bundle"`
	Order   []string       `json:"order"`
	Entries []PreviewEntry `json:"entries"`
}

const previewLedgerPath = "/app/state/preview-ledger.json"

// WritePreviewLedger persists import-preview using manifest declaration order
// (broken — contract requires UTF-8 lexicographic order).
func WritePreviewLedger(bundleDir string, members []Member, manifestOrder []string) error {
	entries := make([]PreviewEntry, 0, len(members))
	order := make([]string, 0, len(members))
	byRaw := make(map[string]Member, len(members))
	for _, m := range members {
		byRaw[m.Raw] = m
	}
	for _, raw := range manifestOrder {
		m, ok := byRaw[raw]
		if !ok {
			continue
		}
		if m.Canonical == "MANIFEST.json" || m.Canonical == ".signatures.json" {
			continue
		}
		entries = append(entries, PreviewEntry{Raw: m.Raw, Canonical: m.Canonical})
		order = append(order, m.Canonical)
	}
	ledger := PreviewLedger{Bundle: bundleDir, Order: order, Entries: entries}
	if err := os.MkdirAll(filepath.Dir(previewLedgerPath), 0o755); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(ledger, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(previewLedgerPath, raw, 0o644)
}

func LoadPreviewLedger() (*PreviewLedger, error) {
	raw, err := os.ReadFile(previewLedgerPath)
	if err != nil {
		return nil, err
	}
	var ledger PreviewLedger
	if err := json.Unmarshal(raw, &ledger); err != nil {
		return nil, err
	}
	return &ledger, nil
}
''',
    )

    # digest: always use manifest order — ignore ledger (broken)
    write(
        ENV / "internal/verify/digest.go",
        r'''package verify

import (
	"crypto/sha256"
	"encoding/hex"

	"github.com/terminus/bundlectl/internal/bundle"
)

func MemberDigest(content []byte) string {
	h := sha256.Sum256(content)
	return hex.EncodeToString(h[:])
}

// ChainRoot uses manifest declaration order (broken — must follow preview ledger lex order).
func ChainRoot(members []bundle.Member, manifestOrder []string) (string, map[string]string) {
	order := make([]bundle.Member, 0, len(members))
	byRaw := make(map[string]bundle.Member, len(members))
	for _, m := range members {
		byRaw[m.Raw] = m
	}
	if len(manifestOrder) > 0 {
		for _, raw := range manifestOrder {
			if m, ok := byRaw[raw]; ok {
				order = append(order, m)
			}
		}
	} else {
		order = append(order, members...)
	}
	digests := make(map[string]string, len(order))
	state := sha256.Sum256(nil)
	for _, m := range order {
		fd := sha256.Sum256(m.Bytes)
		digests[m.Canonical] = hex.EncodeToString(fd[:])
		h := sha256.New()
		h.Write(state[:])
		h.Write([]byte(m.Canonical))
		h.Write(fd[:])
		copy(state[:], h.Sum(nil))
	}
	return hex.EncodeToString(state[:]), digests
}

func SortedChainRoot(members []bundle.Member) (string, map[string]string) {
	return ChainRoot(members, nil)
}
''',
    )

    # canonical: no .. collapse / escape reject
    write(
        ENV / "internal/bundle/canonical.go",
        r'''package bundle

import (
	"strings"
)

// CanonicalPath is intentionally weak: it does not collapse ".." or reject escapes.
func CanonicalPath(path string) (string, error) {
	p := strings.ReplaceAll(path, "\\", "/")
	p = strings.TrimPrefix(p, "./")
	return p, nil
}
''',
    )

    # revoke: compare against fingerprint instead of key_id (broken)
    write(
        ENV / "internal/verify/revoke.go",
        r'''package verify

import (
	"encoding/json"
	"os"
	"path/filepath"
)

type RevokedFile struct {
	Revoked []struct {
		KeyID       string `json:"key_id"`
		Fingerprint string `json:"fingerprint"`
	} `json:"revoked"`
}

func IsRevoked(bundleDir, keyID string) (bool, error) {
	raw, err := os.ReadFile(filepath.Join(bundleDir, "trust/revoked-keys.json"))
	if err != nil {
		return false, err
	}
	var rf RevokedFile
	if err := json.Unmarshal(raw, &rf); err != nil {
		return false, err
	}
	for _, r := range rf.Revoked {
		// Broken: compares key_id against fingerprint.
		if keyID == r.Fingerprint {
			return true, nil
		}
	}
	return false, nil
}
''',
    )

    # scope: includeMeta true causes wrong scoped roots when meta slips in; also pass wrong order
    write(
        ENV / "internal/verify/scope.go",
        r'''package verify

import (
	"strings"

	"github.com/terminus/bundlectl/internal/bundle"
)

func MembersForScope(all []bundle.Member, scope string, includeMeta bool) []bundle.Member {
	out := make([]bundle.Member, 0)
	for _, m := range all {
		if includeMeta || (m.Canonical != "MANIFEST.json" && m.Canonical != ".signatures.json") {
			if strings.HasPrefix(m.Canonical, scope) || scope == "" {
				out = append(out, m)
			}
		}
	}
	return out
}

func ScopedChainRoot(all []bundle.Member, scope string, manifestOrder []string) string {
	// Broken: includeMeta=true and rely on manifest-order ChainRoot.
	subset := MembersForScope(all, scope, true)
	root, _ := ChainRoot(subset, manifestOrder)
	return root
}
''',
    )

    # trace: skip data.foo bindings (broken)
    write(
        ENV / "internal/eval/trace.go",
        r'''package eval

import (
	"encoding/json"
	"strings"
)

func BuildTrace(expr Expr, data, input map[string]any) Trace {
	bindings := make([]Binding, 0)
	for _, ref := range DataRefs(expr) {
		// Broken: drops the primary data.foo binding.
		if ref == "data.foo" {
			continue
		}
		val, _ := lookup(ref, data, input)
		raw, _ := json.Marshal(val)
		bindings = append(bindings, Binding{Ref: ref, Value: raw})
	}
	if strings.HasPrefix(expr.Left, "input.") || strings.HasPrefix(expr.Right, "input.") {
		for _, side := range []string{expr.Left, expr.Right} {
			if strings.HasPrefix(side, "input.") {
				val, _ := lookup(side, data, input)
				raw, _ := json.Marshal(val)
				bindings = append(bindings, Binding{Ref: side, Value: raw})
			}
		}
	}
	return Trace{
		Bindings: bindings,
		Steps:    []string{"load_data", "eval_expr", "decision"},
	}
}

func lookup(ref string, data, input map[string]any) (any, bool) {
	if strings.HasPrefix(ref, "data.") {
		v, ok := data[strings.TrimPrefix(ref, "data.")]
		return v, ok
	}
	if strings.HasPrefix(ref, "input.") {
		v, ok := input[strings.TrimPrefix(ref, "input.")]
		return v, ok
	}
	return nil, false
}
''',
    )

    # audit: off-by-one binding count
    write(
        ENV / "internal/eval/audit.go",
        r'''package eval

import (
	"encoding/json"
	"os"
)

type EvalAudit struct {
	Bundle       string `json:"bundle"`
	Seed         string `json:"seed"`
	Allow        bool   `json:"allow"`
	BindingCount int    `json:"binding_count"`
}

const evalAuditPath = "/app/state/eval-audit.json"

func WriteEvalAudit(bundleDir, seed string, res *EvalResult) error {
	audit := EvalAudit{
		Bundle:       bundleDir,
		Seed:         seed,
		Allow:        res.Allow,
		BindingCount: len(res.Trace.Bindings) - 1,
	}
	if audit.BindingCount < 0 {
		audit.BindingCount = 0
	}
	raw, err := json.MarshalIndent(audit, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	return os.WriteFile(evalAuditPath, raw, 0o644)
}

func LoadEvalAudit() (*EvalAudit, error) {
	raw, err := os.ReadFile(evalAuditPath)
	if err != nil {
		return nil, err
	}
	var audit EvalAudit
	if err := json.Unmarshal(raw, &audit); err != nil {
		return nil, err
	}
	return &audit, nil
}
''',
    )

    # member LoadMember should use strict canonical for escape — broken uses weak
    write(
        ENV / "internal/bundle/member.go",
        r'''package bundle

import (
	"os"
	"path/filepath"
)

type Member struct {
	Canonical string
	Raw       string
	Bytes     []byte
}

func LoadMember(bundleDir, rawPath string, seedApply func([]byte) []byte) (Member, error) {
	can, err := CanonicalPath(rawPath)
	if err != nil {
		return Member{}, err
	}
	full := filepath.Join(bundleDir, filepath.FromSlash(can))
	b, err := os.ReadFile(full)
	if err != nil {
		full = filepath.Join(bundleDir, filepath.FromSlash(rawPath))
		b, err = os.ReadFile(full)
		if err != nil {
			return Member{}, err
		}
	}
	if seedApply != nil {
		b = seedApply(b)
	}
	return Member{Canonical: can, Raw: rawPath, Bytes: b}, nil
}
''',
    )


def write_golden() -> None:
    write(
        SOL / "golden_canonical.go",
        r'''package bundle

import (
	"fmt"
	"strings"
)

func CanonicalPath(path string) (string, error) {
	p := strings.ReplaceAll(path, "\\", "/")
	p = strings.TrimPrefix(p, "./")
	parts := make([]string, 0)
	for _, part := range strings.Split(p, "/") {
		if part == "" || part == "." {
			continue
		}
		if part == ".." {
			if len(parts) == 0 {
				return "", fmt.Errorf("path escapes bundle root: %s", path)
			}
			parts = parts[:len(parts)-1]
			continue
		}
		parts = append(parts, part)
	}
	return strings.Join(parts, "/"), nil
}
''',
    )

    write(
        SOL / "golden_preview_ledger.go",
        r'''package bundle

import (
	"encoding/json"
	"os"
	"path/filepath"
	"sort"
)

type PreviewEntry struct {
	Raw       string `json:"raw"`
	Canonical string `json:"canonical"`
}

type PreviewLedger struct {
	Bundle  string         `json:"bundle"`
	Order   []string       `json:"order"`
	Entries []PreviewEntry `json:"entries"`
}

const previewLedgerPath = "/app/state/preview-ledger.json"

func WritePreviewLedger(bundleDir string, members []Member, _ []string) error {
	entries := make([]PreviewEntry, 0, len(members))
	canonicals := make([]string, 0, len(members))
	for _, m := range members {
		if m.Canonical == "MANIFEST.json" || m.Canonical == ".signatures.json" {
			continue
		}
		entries = append(entries, PreviewEntry{Raw: m.Raw, Canonical: m.Canonical})
		canonicals = append(canonicals, m.Canonical)
	}
	sort.Strings(canonicals)
	ledger := PreviewLedger{Bundle: bundleDir, Order: canonicals, Entries: entries}
	if err := os.MkdirAll(filepath.Dir(previewLedgerPath), 0o755); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(ledger, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(previewLedgerPath, raw, 0o644)
}

func LoadPreviewLedger() (*PreviewLedger, error) {
	raw, err := os.ReadFile(previewLedgerPath)
	if err != nil {
		return nil, err
	}
	var ledger PreviewLedger
	if err := json.Unmarshal(raw, &ledger); err != nil {
		return nil, err
	}
	return &ledger, nil
}
''',
    )

    write(
        SOL / "files/golden_ingest_preview.go",
        r'''package bundle

func IngestPreview(bundleDir string, members []Member, manifestOrder []string) error {
	return WritePreviewLedger(bundleDir, members, manifestOrder)
}
''',
    )
    write(SOL / "golden_ingest_preview.go", (SOL / "files/golden_ingest_preview.go").read_text(encoding="utf-8"))

    write(
        SOL / "golden_digest.go",
        r'''package verify

import (
	"crypto/sha256"
	"encoding/hex"
	"sort"

	"github.com/terminus/bundlectl/internal/bundle"
)

func MemberDigest(content []byte) string {
	h := sha256.Sum256(content)
	return hex.EncodeToString(h[:])
}

func ChainRoot(members []bundle.Member, _ []string) (string, map[string]string) {
	order := append([]bundle.Member(nil), members...)
	if ledger, err := bundle.LoadPreviewLedger(); err == nil && len(ledger.Order) > 0 {
		byCanon := make(map[string]bundle.Member, len(members))
		for _, m := range members {
			byCanon[m.Canonical] = m
		}
		order = order[:0]
		for _, canon := range ledger.Order {
			if m, ok := byCanon[canon]; ok {
				order = append(order, m)
			}
		}
	} else {
		sort.Slice(order, func(i, j int) bool {
			return order[i].Canonical < order[j].Canonical
		})
	}
	digests := make(map[string]string, len(order))
	state := sha256.Sum256(nil)
	for _, m := range order {
		fd := sha256.Sum256(m.Bytes)
		digests[m.Canonical] = hex.EncodeToString(fd[:])
		h := sha256.New()
		h.Write(state[:])
		h.Write([]byte(m.Canonical))
		h.Write(fd[:])
		copy(state[:], h.Sum(nil))
	}
	return hex.EncodeToString(state[:]), digests
}

func SortedChainRoot(members []bundle.Member) (string, map[string]string) {
	return ChainRoot(members, nil)
}
''',
    )

    write(
        SOL / "golden_scope.go",
        r'''package verify

import (
	"strings"

	"github.com/terminus/bundlectl/internal/bundle"
)

func MembersForScope(all []bundle.Member, scope string, includeMeta bool) []bundle.Member {
	out := make([]bundle.Member, 0)
	for _, m := range all {
		if !includeMeta && (m.Canonical == "MANIFEST.json" || m.Canonical == ".signatures.json") {
			continue
		}
		if scope == "" || strings.HasPrefix(m.Canonical, scope) {
			out = append(out, m)
		}
	}
	return out
}

func ScopedChainRoot(all []bundle.Member, scope string, _ []string) string {
	subset := MembersForScope(all, scope, false)
	root, _ := SortedChainRoot(subset)
	return root
}
''',
    )

    write(
        SOL / "golden_revoke.go",
        r'''package verify

import (
	"encoding/json"
	"os"
	"path/filepath"
)

type RevokedFile struct {
	Revoked []struct {
		KeyID       string `json:"key_id"`
		Fingerprint string `json:"fingerprint"`
	} `json:"revoked"`
}

func IsRevoked(bundleDir, keyID string) (bool, error) {
	raw, err := os.ReadFile(filepath.Join(bundleDir, "trust/revoked-keys.json"))
	if err != nil {
		return false, err
	}
	var rf RevokedFile
	if err := json.Unmarshal(raw, &rf); err != nil {
		return false, err
	}
	for _, r := range rf.Revoked {
		if keyID == r.KeyID {
			return true, nil
		}
	}
	return false, nil
}
''',
    )

    write(
        SOL / "golden_trace.go",
        r'''package eval

import (
	"encoding/json"
	"strings"
)

func BuildTrace(expr Expr, data, input map[string]any) Trace {
	bindings := make([]Binding, 0)
	seen := map[string]bool{}
	for _, ref := range DataRefs(expr) {
		if seen[ref] {
			continue
		}
		seen[ref] = true
		val, _ := lookup(ref, data, input)
		raw, _ := json.Marshal(val)
		bindings = append(bindings, Binding{Ref: ref, Value: raw})
	}
	for _, side := range []string{expr.Left, expr.Right} {
		if strings.HasPrefix(side, "input.") && !seen[side] {
			seen[side] = true
			val, _ := lookup(side, data, input)
			raw, _ := json.Marshal(val)
			bindings = append(bindings, Binding{Ref: side, Value: raw})
		}
		if strings.HasPrefix(side, "data.") && !seen[side] {
			seen[side] = true
			val, _ := lookup(side, data, input)
			raw, _ := json.Marshal(val)
			bindings = append(bindings, Binding{Ref: side, Value: raw})
		}
	}
	return Trace{
		Bindings: bindings,
		Steps:    []string{"load_data", "eval_expr", "decision"},
	}
}

func lookup(ref string, data, input map[string]any) (any, bool) {
	if strings.HasPrefix(ref, "data.") {
		v, ok := data[strings.TrimPrefix(ref, "data.")]
		return v, ok
	}
	if strings.HasPrefix(ref, "input.") {
		v, ok := input[strings.TrimPrefix(ref, "input.")]
		return v, ok
	}
	return nil, false
}
''',
    )

    write(
        SOL / "golden_audit.go",
        r'''package eval

import (
	"encoding/json"
	"os"
)

type EvalAudit struct {
	Bundle       string `json:"bundle"`
	Seed         string `json:"seed"`
	Allow        bool   `json:"allow"`
	BindingCount int    `json:"binding_count"`
}

const evalAuditPath = "/app/state/eval-audit.json"

func WriteEvalAudit(bundleDir, seed string, res *EvalResult) error {
	audit := EvalAudit{
		Bundle:       bundleDir,
		Seed:         seed,
		Allow:        res.Allow,
		BindingCount: len(res.Trace.Bindings),
	}
	raw, err := json.MarshalIndent(audit, "", "  ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	return os.WriteFile(evalAuditPath, raw, 0o644)
}

func LoadEvalAudit() (*EvalAudit, error) {
	raw, err := os.ReadFile(evalAuditPath)
	if err != nil {
		return nil, err
	}
	var audit EvalAudit
	if err := json.Unmarshal(raw, &audit); err != nil {
		return nil, err
	}
	return &audit, nil
}
''',
    )

    write(
        SOL / "solve.sh",
        r'''#!/usr/bin/env bash
set -euo pipefail
SOL=""
for candidate in "$(dirname "$0")" "$(dirname "$0")/files" /solution /oracle/solution; do
  if [ -f "${candidate}/golden_digest.go" ]; then
    SOL="${candidate}"
    break
  fi
done
if [ -z "${SOL}" ]; then
  echo "golden sources not found" >&2
  exit 1
fi
cp -f "${SOL}/golden_canonical.go" /app/internal/bundle/canonical.go
cp -f "${SOL}/files/golden_ingest_preview.go" /app/internal/bundle/ingest_preview.go 2>/dev/null \
  || cp -f "${SOL}/golden_ingest_preview.go" /app/internal/bundle/ingest_preview.go
cp -f "${SOL}/golden_preview_ledger.go" /app/internal/bundle/preview_ledger.go
cp -f "${SOL}/golden_digest.go" /app/internal/verify/digest.go
cp -f "${SOL}/golden_scope.go" /app/internal/verify/scope.go
cp -f "${SOL}/golden_revoke.go" /app/internal/verify/revoke.go
cp -f "${SOL}/golden_trace.go" /app/internal/eval/trace.go
cp -f "${SOL}/golden_audit.go" /app/internal/eval/audit.go
export PATH="/usr/local/go/bin:${PATH}"
cd /app
go build -mod=readonly -o /usr/local/bin/bundlectl ./cmd/bundlectl
''',
    )


def write_stubs() -> None:
    # copy goldens used as partial-fix stubs
    for name in (
        "golden_digest.go",
        "golden_trace.go",
        "golden_preview_ledger.go",
    ):
        write(STUBS / name, (SOL / name).read_text(encoding="utf-8"))
    write(STUBS / "broken_digest.go", (ENV / "internal/verify/digest.go").read_text(encoding="utf-8"))
    write(STUBS / "broken_trace.go", (ENV / "internal/eval/trace.go").read_text(encoding="utf-8"))


def write_dockerfile() -> None:
    write(
        ENV / "Dockerfile",
        r'''FROM public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac

COPY requirements.txt /tmp/requirements.txt
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    asciinema \
    ca-certificates \
    python3 \
    python3-pip \
    python3-venv \
    tmux \
 && rm -rf /var/lib/apt/lists/* \
 && python3 -m venv /opt/verifier-venv \
 && /opt/verifier-venv/bin/pip install --no-cache-dir --require-hashes -r /tmp/requirements.txt \
 && rm -f /tmp/requirements.txt

ENV PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/go/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ENV CGO_ENABLED=0

WORKDIR /app
COPY go.mod /app/go.mod
COPY cmd/ /app/cmd/
COPY internal/ /app/internal/
COPY docs/ /app/docs/
COPY tools/ /app/tools/
COPY scripts/ /app/scripts/
COPY trust/ /app/trust/
COPY README.md /app/README.md
COPY opt-seed/verifier-fixtures/ /opt/verifier-fixtures/

RUN chmod +x /app/scripts/gen-fixtures.sh /app/scripts/reset-state.sh /app/scripts/rebuild-bundlectl.sh \
 && /app/scripts/gen-fixtures.sh \
 && mkdir -p /app/output /app/state
''',
    )


def write_task_toml() -> None:
    write(
        TASK / "task.toml",
        r'''version = "2.0"

[metadata]
author_name = "anonymous"
author_email = "anonymous@gmail.com"
difficulty = "medium"
category = "security"
subcategories = []
number_of_milestones = 0
codebase_size = "small"
languages = ["go"]
tags = ["opa", "bundle", "signature", "digest", "chain", "verifier"]
expert_time_estimate_min = 240
junior_time_estimate_min = 480

[agent]
timeout_sec = 1800

[verifier]
timeout_sec = 900

[environment]
allow_internet = false
build_timeout_sec = 900.0
cpus = 2
memory_mb = 4096
storage_mb = 10240
workdir = "/app"
''',
    )


def write_test_sh() -> None:
    write(
        TESTS / "test.sh",
        r'''#!/usr/bin/env bash
set -uo pipefail

export PATH="/usr/local/go/bin:/opt/verifier-venv/bin:/usr/local/bin:${PATH}"
export CGO_ENABLED=0
TEST_DIR="${TEST_DIR:-/tests}"

mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\n' > /logs/verifier/ctrf.json

if [ "$PWD" = "/" ]; then
  echo "Error: No working directory set. Please set a WORKDIR in your Dockerfile."
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi

cd /app || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}

sed -i 's/\r$//' "${TEST_DIR}"/*.py "${TEST_DIR}"/*.sh 2>/dev/null || true
bash /app/scripts/reset-state.sh >/dev/null 2>&1 || true
if ! bash /app/scripts/rebuild-bundlectl.sh; then
  echo 0 > /logs/verifier/reward.txt
  exit 1
fi

set +e
cd "${TEST_DIR}" || {
  echo 0 > /logs/verifier/reward.txt
  exit 1
}
/opt/verifier-venv/bin/pytest -o cache_dir=/tmp/pytest_cache \
  --ctrf /logs/verifier/ctrf.json \
  "${TEST_DIR}/test_outputs.py" \
  -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
''',
    )


def main() -> None:
    patch_gen_fixtures()
    seed = (ENV / "internal/seed/seed.go").read_text(encoding="utf-8")
    seed = seed.replace(
        "opa-bundle-signature-digest-chain-verifier-repair",
        "opa-bundle-signature-digest-chain-verifier",
    )
    write(ENV / "internal/seed/seed.go", seed)

    ipc = (ENV / "docs/import-preview-contract.md").read_text(encoding="utf-8")
    ipc = ipc.replace(
        "Trap bundles (`tampered-member`, `revoked-signer`, `bad-scope-chain`) must fail verify.",
        "Trap bundles (`tampered-member`, `revoked-signer`, `bad-scope-chain`, `path-escape`) must fail verify.",
    )
    write(ENV / "docs/import-preview-contract.md", ipc)

    write_broken_sources()
    write_golden()
    write_stubs()
    write_dockerfile()
    write_task_toml()
    write_test_sh()
    print("core rebuild done")


if __name__ == "__main__":
    main()
