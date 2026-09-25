#!/usr/bin/env python3
"""Bootstrap duckdb-storage-segment-attach-catalog-watermark-merger task tree."""
from __future__ import annotations

import json
import hashlib
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TASK = REPO / "tasks" / "duckdb-segment-attach-catalog-watermark-atlas"
ENV = TASK / "environment"

GO_MOD = """module duckcatalog

go 1.22
"""

MAIN_GO = r'''package main

import (
	"fmt"
	"os"

	"duckcatalog/internal/export"
	"duckcatalog/internal/ingest"
	"duckcatalog/internal/staging"
)

func usage() {
	fmt.Fprintln(os.Stderr, "usage: duckcatalog attach|seal ...")
}

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "attach":
		if err := runAttach(os.Args[2:]); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	case "seal":
		if err := runSeal(os.Args[2:]); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	default:
		usage()
		os.Exit(2)
	}
}

func runAttach(args []string) error {
	batches := ""
	atlas := ""
	resume := ""
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--batches":
			if i+1 >= len(args) {
				return fmt.Errorf("missing value for --batches")
			}
			i++
			batches = args[i]
		case "--atlas":
			if i+1 >= len(args) {
				return fmt.Errorf("missing value for --atlas")
			}
			i++
			atlas = args[i]
		case "--resume":
			if i+1 >= len(args) {
				return fmt.Errorf("missing value for --resume")
			}
			i++
			resume = args[i]
		default:
			return fmt.Errorf("unknown flag %s", args[i])
		}
	}
	if batches == "" || atlas == "" {
		return fmt.Errorf("missing required flags")
	}
	rows, err := ingest.ReadAttachJSONL(batches)
	if err != nil {
		return err
	}
	return staging.ReplayAttach(rows, atlas, resume)
}

func runSeal(args []string) error {
	atlas := ""
	output := ""
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--atlas":
			if i+1 >= len(args) {
				return fmt.Errorf("missing value for --atlas")
			}
			i++
			atlas = args[i]
		case "--output":
			if i+1 >= len(args) {
				return fmt.Errorf("missing value for --output")
			}
			i++
			output = args[i]
		default:
			return fmt.Errorf("unknown flag %s", args[i])
		}
	}
	if atlas == "" || output == "" {
		return fmt.Errorf("missing required flags")
	}
	snap, err := staging.LoadAtlas(atlas)
	if err != nil {
		return err
	}
	return export.SealAtlas(snap, output)
}
'''

MODEL_GO = '''package model

const SchemaVersion = 2

type AttachRow struct {
	CatalogID    string `json:"catalog_id"`
	TableName    string `json:"table_name"`
	SegmentUUID  string `json:"segment_uuid"`
	FileOffset   int64  `json:"file_offset"`
	AttachSeq    int64  `json:"attach_seq"`
	Generation   int64  `json:"generation"`
	ColumnName   string `json:"column_name"`
	LogicalType  string `json:"logical_type"`
	TypeWidth    int    `json:"type_width"`
	StatValue    string `json:"stat_value"`
	IsDeleted    int    `json:"is_deleted"`
	CheckpointGen int64 `json:"checkpoint_gen"`
}

type Watermark struct {
	CatalogID      string `json:"catalog_id"`
	TableName      string `json:"table_name"`
	CheckpointGen  int64  `json:"checkpoint_gen"`
	MaxGeneration  int64  `json:"max_generation"`
}

type Atlas struct {
	SchemaVersion int          `json:"schema_version"`
	Watermarks    []Watermark  `json:"watermarks"`
	Rows          []AttachRow  `json:"rows"`
	AtlasDigest   string       `json:"atlas_digest"`
}

type ManifestEntry struct {
	CatalogID     string `json:"catalog_id"`
	TableName     string `json:"table_name"`
	ColumnName    string `json:"column_name"`
	LogicalType   string `json:"logical_type"`
	TypeWidth     int    `json:"type_width"`
	SegmentUUID   string `json:"segment_uuid"`
	Generation    int64  `json:"generation"`
	IsDeleted     int    `json:"is_deleted"`
	StatValue     string `json:"stat_value"`
	EntrySHA256   string `json:"entry_sha256"`
}

type SealedManifest struct {
	Entries          []ManifestEntry `json:"entries"`
	AtlasRootSHA256  string          `json:"atlas_root_sha256"`
}
'''

UTIL_GO = '''package util

import (
	"crypto/sha256"
	"encoding/hex"
	"duckcatalog/internal/model"
	"sort"
)

func SHA256Hex(data []byte) string {
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:])
}

func StatKey(r model.AttachRow) string {
	return r.CatalogID + "|" + r.TableName + "|" + r.ColumnName + "|" + r.LogicalType + "|" + itoa(r.TypeWidth)
}

func itoa(v int) string {
	if v == 0 {
		return "0"
	}
	neg := v < 0
	if neg {
		v = -v
	}
	buf := make([]byte, 0, 12)
	for v > 0 {
		buf = append(buf, byte('0'+v%10))
		v /= 10
	}
	for i, j := 0, len(buf)-1; i < j; i, j = i+1, j-1 {
		buf[i], buf[j] = buf[j], buf[i]
	}
	if neg {
		return "-" + string(buf)
	}
	return string(buf)
}

func RowBeats(a, b model.AttachRow) bool {
	if a.Generation != b.Generation {
		return a.Generation > b.Generation
	}
	if a.AttachSeq != b.AttachSeq {
		return a.AttachSeq > b.AttachSeq
	}
	return a.SegmentUUID > b.SegmentUUID
}

func CompareRows(a, b model.AttachRow) int {
	ka := StatKey(a)
	kb := StatKey(b)
	if ka < kb {
		return -1
	}
	if ka > kb {
		return 1
	}
	return 0
}

func SortRows(rows []model.AttachRow) {
	sort.Slice(rows, func(i, j int) bool {
		return CompareRows(rows[i], rows[j]) < 0
	})
}

func SortWatermarks(w []model.Watermark) {
	sort.Slice(w, func(i, j int) bool {
		if w[i].CatalogID != w[j].CatalogID {
			return w[i].CatalogID < w[j].CatalogID
		}
		return w[i].TableName < w[j].TableName
	})
}

func EntryHash(r model.AttachRow, includeTypeBits bool) string {
	canon := r.CatalogID + "|" + r.TableName + "|" + r.ColumnName + "|" + r.SegmentUUID + "|" +
		itoa64(r.Generation) + "|" + itoa(r.IsDeleted) + "|" + r.StatValue
	if includeTypeBits {
		canon += "|" + r.LogicalType + "|" + itoa(r.TypeWidth)
	}
	return SHA256Hex([]byte(canon))
}

func itoa64(v int64) string {
	if v == 0 {
		return "0"
	}
	neg := v < 0
	if neg {
		v = -v
	}
	buf := make([]byte, 0, 20)
	for v > 0 {
		buf = append(buf, byte('0'+v%10))
		v /= 10
	}
	for i, j := 0, len(buf)-1; i < j; i, j = i+1, j-1 {
		buf[i], buf[j] = buf[j], buf[i]
	}
	if neg {
		return "-" + string(buf)
	}
	return string(buf)
}

func AtlasDigest(w []model.Watermark, rows []model.AttachRow) string {
	wcopy := append([]model.Watermark(nil), w...)
	SortWatermarks(wcopy)
	rcopy := append([]model.AttachRow(nil), rows...)
	SortRows(rcopy)
	lines := ""
	for _, wm := range wcopy {
		lines += wm.CatalogID + "|" + wm.TableName + "|" + itoa64(wm.CheckpointGen) + "|" + itoa64(wm.MaxGeneration) + "\n"
	}
	for _, r := range rcopy {
		lines += StatKey(r) + "|" + r.SegmentUUID + "|" + itoa64(r.AttachSeq) + "|" + itoa64(r.Generation) + "|" +
			itoa(r.IsDeleted) + "|" + r.StatValue + "\n"
	}
	return SHA256Hex([]byte(lines))
}
'''

# Broken modules - markers BROKEN_* in comments for clarity
INGEST_BROKEN = '''package ingest

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"duckcatalog/internal/model"
)

func ReadAttachJSONL(path string) ([]model.AttachRow, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open batches: %w", err)
	}
	defer f.Close()
	var rows []model.AttachRow
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := sc.Text()
		if line == "" {
			continue
		}
		var r model.AttachRow
		if err := json.Unmarshal([]byte(line), &r); err != nil {
			return nil, fmt.Errorf("parse jsonl: %w", err)
		}
		rows = append(rows, r)
	}
	if err := sc.Err(); err != nil {
		return nil, err
	}
	// BROKEN: rank by file_offset not attach_seq before downstream coalesce
	sort.SliceStable(rows, func(i, j int) bool {
		if rows[i].FileOffset != rows[j].FileOffset {
			return rows[i].FileOffset < rows[j].FileOffset
		}
		return rows[i].SegmentUUID < rows[j].SegmentUUID
	})
	return rows, nil
}
'''

INGEST_GOLDEN = '''package ingest

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"duckcatalog/internal/model"
)

func ReadAttachJSONL(path string) ([]model.AttachRow, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("open batches: %w", err)
	}
	defer f.Close()
	var rows []model.AttachRow
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := sc.Text()
		if line == "" {
			continue
		}
		var r model.AttachRow
		if err := json.Unmarshal([]byte(line), &r); err != nil {
			return nil, fmt.Errorf("parse jsonl: %w", err)
		}
		rows = append(rows, r)
	}
	if err := sc.Err(); err != nil {
		return nil, err
	}
	sort.SliceStable(rows, func(i, j int) bool {
		if rows[i].AttachSeq != rows[j].AttachSeq {
			return rows[i].AttachSeq < rows[j].AttachSeq
		}
		return rows[i].SegmentUUID < rows[j].SegmentUUID
	})
	return rows, nil
}
'''

NORMALIZE_BROKEN = '''package normalize

import (
	"duckcatalog/internal/model"
	"duckcatalog/internal/util"
)

func CoalesceStats(rows []model.AttachRow) []model.AttachRow {
	best := map[string]model.AttachRow{}
	for _, r := range rows {
		// BROKEN: key column name only
		k := r.CatalogID + "|" + r.TableName + "|" + r.ColumnName
		if prev, ok := best[k]; !ok || rowWinsBroken(r, prev) {
			best[k] = r
		}
	}
	out := make([]model.AttachRow, 0, len(best))
	for _, r := range best {
		out = append(out, r)
	}
	util.SortRows(out)
	return out
}

func rowWinsBroken(a, b model.AttachRow) bool {
	if a.AttachSeq != b.AttachSeq {
		return a.AttachSeq > b.AttachSeq
	}
	return a.SegmentUUID > b.SegmentUUID
}
'''

NORMALIZE_GOLDEN = '''package normalize

import (
	"duckcatalog/internal/model"
	"duckcatalog/internal/util"
)

func CoalesceStats(rows []model.AttachRow) []model.AttachRow {
	best := map[string]model.AttachRow{}
	for _, r := range rows {
		k := util.StatKey(r)
		if prev, ok := best[k]; !ok || util.RowBeats(r, prev) {
			best[k] = r
		}
	}
	out := make([]model.AttachRow, 0, len(best))
	for _, r := range best {
		out = append(out, r)
	}
	util.SortRows(out)
	return out
}
'''

STAGING_BROKEN = '''package staging

import (
	"encoding/json"
	"fmt"
	"os"

	"duckcatalog/internal/model"
	"duckcatalog/internal/normalize"
	"duckcatalog/internal/state"
	"duckcatalog/internal/util"
)

func ReplayAttach(batch []model.AttachRow, atlasPath, resumePath string) error {
	snap := model.Atlas{SchemaVersion: model.SchemaVersion, Watermarks: []model.Watermark{}, Rows: []model.AttachRow{}}
	if resumePath != "" {
		prev, err := LoadAtlas(resumePath)
		if err != nil {
			return err
		}
		snap.Watermarks = state.MergeWatermarks(snap.Watermarks, prev.Watermarks)
		snap.Rows = append(snap.Rows, prev.Rows...)
		batch = state.FilterByResume(batch, prev)
	}
	coalesced := normalize.CoalesceStats(batch)
	// BROKEN: empty batch clears watermarks
	if len(batch) == 0 {
		snap.Watermarks = []model.Watermark{}
	} else {
		snap.Watermarks = updateWatermarks(snap.Watermarks, coalesced)
	}
	merged := append(snap.Rows, coalesced...)
	snap.Rows = normalize.CoalesceStats(merged)
	snap.AtlasDigest = util.AtlasDigest(snap.Watermarks, snap.Rows)
	return writeAtlas(atlasPath, snap)
}

func updateWatermarks(base []model.Watermark, rows []model.AttachRow) []model.Watermark {
	idx := map[string]model.Watermark{}
	for _, w := range base {
		idx[w.CatalogID+"|"+w.TableName] = w
	}
	for _, r := range rows {
		k := r.CatalogID + "|" + r.TableName
		w := idx[k]
		w.CatalogID = r.CatalogID
		w.TableName = r.TableName
		if r.CheckpointGen > w.CheckpointGen {
			w.CheckpointGen = r.CheckpointGen
		}
		if r.Generation > w.MaxGeneration {
			w.MaxGeneration = r.Generation
		}
		idx[k] = w
	}
	out := make([]model.Watermark, 0, len(idx))
	for _, w := range idx {
		out = append(out, w)
	}
	util.SortWatermarks(out)
	return out
}

func LoadAtlas(path string) (model.Atlas, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return model.Atlas{}, err
	}
	var snap model.Atlas
	if err := json.Unmarshal(data, &snap); err != nil {
		return model.Atlas{}, fmt.Errorf("parse atlas: %w", err)
	}
	return snap, nil
}

func writeAtlas(path string, snap model.Atlas) error {
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	data, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	return os.WriteFile(path, data, 0o644)
}
'''

STAGING_GOLDEN = STAGING_BROKEN.replace(
	'''	// BROKEN: empty batch clears watermarks
	if len(batch) == 0 {
		snap.Watermarks = []model.Watermark{}
	} else {
		snap.Watermarks = updateWatermarks(snap.Watermarks, coalesced)
	}''',
	'''	if len(batch) > 0 {
		snap.Watermarks = updateWatermarks(snap.Watermarks, coalesced)
	}''',
)

EXPORT_BROKEN = '''package export

import (
	"encoding/json"
	"fmt"
	"os"

	"duckcatalog/internal/model"
	"duckcatalog/internal/util"
)

func SealAtlas(snap model.Atlas, output string) error {
	entries := make([]model.ManifestEntry, 0, len(snap.Rows))
	for _, r := range snap.Rows {
		// BROKEN: omit type bits in hash
		h := util.EntryHash(r, false)
		entries = append(entries, model.ManifestEntry{
			CatalogID:   r.CatalogID,
			TableName:   r.TableName,
			ColumnName:  r.ColumnName,
			LogicalType: r.LogicalType,
			TypeWidth:   r.TypeWidth,
			SegmentUUID: r.SegmentUUID,
			Generation:  r.Generation,
			IsDeleted:   r.IsDeleted,
			StatValue:   r.StatValue,
			EntrySHA256: h,
		})
	}
	rootLines := ""
	for _, e := range entries {
		rootLines += e.EntrySHA256 + "\n"
	}
	root := util.SHA256Hex([]byte(rootLines))
	out := model.SealedManifest{Entries: entries, AtlasRootSHA256: root}
	data, err := json.MarshalIndent(out, "", "  ")
	if err != nil {
		return err
	}
	data = append(data, '\n')
	if err := os.MkdirAll("/app/output", 0o755); err != nil {
		return err
	}
	return os.WriteFile(output, data, 0o644)
}
'''

EXPORT_GOLDEN = EXPORT_BROKEN.replace("util.EntryHash(r, false)", "util.EntryHash(r, true)").replace(
	"// BROKEN: omit type bits in hash\n\t\t", ""
)

RESUME_BROKEN = '''package state

import (
	"duckcatalog/internal/model"
	"duckcatalog/internal/util"
)

func MergeWatermarks(base, prev []model.Watermark) []model.Watermark {
	idx := map[string]model.Watermark{}
	for _, w := range base {
		idx[w.CatalogID+"|"+w.TableName] = w
	}
	for _, w := range prev {
		k := w.CatalogID + "|" + w.TableName
		if cur, ok := idx[k]; !ok || w.CheckpointGen > cur.CheckpointGen {
			idx[k] = w
		} else if w.CheckpointGen == cur.CheckpointGen && w.MaxGeneration > cur.MaxGeneration {
			idx[k] = w
		}
	}
	out := make([]model.Watermark, 0, len(idx))
	for _, w := range idx {
		out = append(out, w)
	}
	util.SortWatermarks(out)
	return out
}

func watermarkForRow(prev model.Atlas, r model.AttachRow) int64 {
	for _, w := range prev.Watermarks {
		if w.CatalogID == r.CatalogID && w.TableName == r.TableName {
			return w.MaxGeneration
		}
	}
	return -1
}

func FilterByResume(batch []model.AttachRow, prev model.Atlas) []model.AttachRow {
	out := make([]model.AttachRow, 0, len(batch))
	for _, r := range batch {
		wm := watermarkForRow(prev, r)
		// BROKEN: inverted filter drops generation >= watermark
		if wm >= 0 && r.Generation >= wm {
			continue
		}
		out = append(out, r)
	}
	return out
}
'''

RESUME_GOLDEN = RESUME_BROKEN.replace(
	'''		// BROKEN: inverted filter drops generation >= watermark
		if wm >= 0 && r.Generation >= wm {
			continue
		}''',
	'''		if wm >= 0 && r.Generation < wm {
			continue
		}''',
)

DECOY = '''package legacy

import "duckcatalog/internal/model"

func TypeWidthCompat(rows []model.AttachRow) int {
	_ = rows
	return 0
}
'''

BUILD_FIXTURES = '''#!/usr/bin/env python3
"""Generate bundled attach fixtures."""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
import sys

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "/app/fixtures/attach")


def w(path: Path, rows: list[dict]) -> None:
    path.write_text("\\n".join(json.dumps(r) for r in rows) + "\\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    w(OUT / "basic_attach.jsonl", [
        {"catalog_id": "main", "table_name": "events", "segment_uuid": "seg-alpha", "file_offset": 8192,
         "attach_seq": 2, "generation": 5, "column_name": "user_id", "logical_type": "INT64", "type_width": 64,
         "stat_value": "1000", "is_deleted": 0, "checkpoint_gen": 3},
        {"catalog_id": "main", "table_name": "events", "segment_uuid": "seg-bravo", "file_offset": 4096,
         "attach_seq": 1, "generation": 4, "column_name": "user_id", "logical_type": "INT64", "type_width": 64,
         "stat_value": "900", "is_deleted": 0, "checkpoint_gen": 3},
    ])
    w(OUT / "attach_seq_tie.jsonl", [
        {"catalog_id": "main", "table_name": "metrics", "segment_uuid": "seg-low", "file_offset": 9000,
         "attach_seq": 1, "generation": 7, "column_name": "latency", "logical_type": "DOUBLE", "type_width": 64,
         "stat_value": "1.1", "is_deleted": 0, "checkpoint_gen": 2},
        {"catalog_id": "main", "table_name": "metrics", "segment_uuid": "seg-zulu", "file_offset": 1000,
         "attach_seq": 9, "generation": 7, "column_name": "latency", "logical_type": "DOUBLE", "type_width": 64,
         "stat_value": "2.2", "is_deleted": 0, "checkpoint_gen": 2},
    ])
    w(OUT / "typed_stat_collision.jsonl", [
        {"catalog_id": "main", "table_name": "dims", "segment_uuid": "seg-t1", "file_offset": 100,
         "attach_seq": 1, "generation": 3, "column_name": "id", "logical_type": "INT32", "type_width": 32,
         "stat_value": "10", "is_deleted": 1, "checkpoint_gen": 1},
        {"catalog_id": "main", "table_name": "dims", "segment_uuid": "seg-t2", "file_offset": 200,
         "attach_seq": 2, "generation": 4, "column_name": "id", "logical_type": "INT64", "type_width": 64,
         "stat_value": "99", "is_deleted": 0, "checkpoint_gen": 1},
    ])
    w(OUT / "resume_seed.jsonl", [
        {"catalog_id": "main", "table_name": "facts", "segment_uuid": "seg-r1", "file_offset": 500,
         "attach_seq": 1, "generation": 10, "column_name": "amount", "logical_type": "INT64", "type_width": 64,
         "stat_value": "50", "is_deleted": 0, "checkpoint_gen": 8},
    ])
    w(OUT / "empty_batch.jsonl", [])
    w(OUT / "corrupt.jsonl", ["{not json"])
    manifest = {"files": sorted(p.name for p in OUT.glob("*.jsonl"))}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\\n", encoding="utf-8")
    digests = {f"fixtures/attach/{n}": hashlib.sha256((OUT / n).read_bytes()).hexdigest() for n in manifest["files"]}
    (OUT / "digests.json").write_text(json.dumps(digests, indent=2) + "\\n", encoding="utf-8")


if __name__ == "__main__":
    main()
'''

BUILD_HIDDEN = '''#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
import sys

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "/opt/verifier-fixtures/attach")


def w(path: Path, rows: list[dict]) -> None:
    path.write_text("\\n".join(json.dumps(r) for r in rows) + "\\n", encoding="utf-8")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    w(OUT / "hidden_attach_seq_tie.jsonl", [
        {"catalog_id": "main", "table_name": "hidden", "segment_uuid": "seg-a", "file_offset": 50000,
         "attach_seq": 3, "generation": 11, "column_name": "col", "logical_type": "VARCHAR", "type_width": 256,
         "stat_value": "x", "is_deleted": 0, "checkpoint_gen": 5},
        {"catalog_id": "main", "table_name": "hidden", "segment_uuid": "seg-zulu", "file_offset": 100,
         "attach_seq": 99, "generation": 11, "column_name": "col", "logical_type": "VARCHAR", "type_width": 256,
         "stat_value": "y", "is_deleted": 0, "checkpoint_gen": 5},
    ])
    w(OUT / "hidden_type_width_digest.jsonl", [
        {"catalog_id": "main", "table_name": "acct", "segment_uuid": "seg-d1", "file_offset": 10,
         "attach_seq": 1, "generation": 6, "column_name": "bal", "logical_type": "INT32", "type_width": 32,
         "stat_value": "0", "is_deleted": 1, "checkpoint_gen": 4},
        {"catalog_id": "main", "table_name": "acct", "segment_uuid": "seg-live", "file_offset": 20,
         "attach_seq": 2, "generation": 7, "column_name": "bal", "logical_type": "INT32", "type_width": 32,
         "stat_value": "42", "is_deleted": 0, "checkpoint_gen": 4},
    ])
    w(OUT / "hidden_resume_batch1.jsonl", [
        {"catalog_id": "main", "table_name": "evt", "segment_uuid": "p-101", "file_offset": 1,
         "attach_seq": 1, "generation": 20, "column_name": "k", "logical_type": "INT64", "type_width": 64,
         "stat_value": "1", "is_deleted": 0, "checkpoint_gen": 15},
    ])
    w(OUT / "hidden_resume_batch2.jsonl", [
        {"catalog_id": "main", "table_name": "evt", "segment_uuid": "p-102", "file_offset": 2,
         "attach_seq": 2, "generation": 20, "column_name": "k", "logical_type": "INT64", "type_width": 64,
         "stat_value": "2", "is_deleted": 0, "checkpoint_gen": 15},
    ])


if __name__ == "__main__":
    main()
'''

INSTRUCTION = """Implement the duckcatalog DuckDB storage segment attach catalog watermark CLI at /usr/local/bin/duckcatalog and complete the Go sources under /app/. The tool decodes JSONL segment attach batches from /app/fixtures/attach/, persists a catalog watermark atlas at /app/state/catalog-watermark-atlas.json, and emits a sealed attach manifest to /app/output/sealed-attach-manifest.json.

Behavioral contracts live in /app/docs/attach-batch-schema.md, /app/docs/stat-tombstone-coalesce.md, /app/docs/catalog-watermark-schema.md, /app/docs/sealed-manifest-schema.md, /app/docs/cli-surface.md, /app/docs/fixture-catalog.md, and /app/docs/module-api.md. Bundled fixtures are under /app/fixtures/attach/. When TB3_FIXTURES_DIR points at an absolute directory under /opt/verifier-fixtures/attach/, the same attach-normalize-seal pipeline must handle those hidden fixtures with matching atlas digests and manifest checksums.

The CLI must quarantine missing or corrupt JSONL with exit 1. Missing required flags exit 2. Seal must read only the catalog watermark atlas and must not reopen attach fixture files. Rebuild with go build -o /usr/local/bin/duckcatalog ./cmd/duckcatalog after source edits. Do not run apt-get, pip install, or other network installs.

Do not edit /app/docs/, /app/fixtures/, or /app/tools/."""

TASK_TOML = """version = "2.0"

[metadata]
author_name = "anonymous"
author_email = "anonymous"
difficulty = "hard"
category = "data-processing"
subcategories = []
number_of_milestones = 0
codebase_size = "small"
languages = ["go", "bash"]
tags = ["duckdb", "attach", "catalog", "watermark", "segment", "go-cli", "olap"]
expert_time_estimate_min = 240
junior_time_estimate_min = 520

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
"""

DOCKERFILE = """FROM public.ecr.aws/docker/library/golang:1.22-bookworm@sha256:1cf585c514cb703a8c3a2a9c5c9a1c5e4e8b8e8e8e8e8e8e8e8e8e8e8e8e8e8

"""

# Need correct golang ECR digest - read from canonical gate or dgraph uses debian + build go
# Use debian + golang from apt like other go tasks

DOCKERFILE = """FROM public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d

RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        bash ca-certificates tmux asciinema python3 python3-pip python3-venv \\
        golang-go git coreutils \\
    && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/verifier-venv \\
    && /opt/verifier-venv/bin/pip install --no-cache-dir pytest==8.4.1 pytest-json-ctrf==0.3.5

WORKDIR /app
COPY go.mod ./
COPY cmd/ ./cmd/
COPY internal/ ./internal/
COPY docs/ ./docs/
COPY scripts/ ./scripts/
COPY tools/ ./tools/

RUN mkdir -p /app/fixtures/attach /app/state /app/output /opt/verifier-fixtures/attach \\
        /opt/verifier-broken-duckcatalog-src \\
    && find /app/scripts /app/tools -name '*.py' -exec sed -i 's/\\r$//' {} + \\
    && find /app/scripts -name '*.sh' -exec sed -i 's/\\r$//' {} + \\
    && chmod +x /app/scripts/*.sh /app/tools/*.py \\
    && python3 /app/tools/build_fixtures.py /app/fixtures/attach \\
    && python3 /app/tools/build_hidden_fixtures.py /opt/verifier-fixtures/attach \\
    && cp -a /app/internal/. /opt/verifier-broken-duckcatalog-src/internal/ \\
    && cp -a /app/cmd/. /opt/verifier-broken-duckcatalog-src/cmd/ \\
    && go build -o /usr/local/bin/duckcatalog ./cmd/duckcatalog

ENV PATH="/usr/local/bin:/app:${PATH}"
ENV GO111MODULE=on
"""

RESET_SH = """#!/usr/bin/env bash
set -euo pipefail
rm -f /app/state/catalog-watermark-atlas.json /app/output/sealed-attach-manifest.json
mkdir -p /app/state /app/output
"""

SOLVE_SH = """#!/usr/bin/env bash
set -euo pipefail
APP_ROOT="${APP_ROOT:-/app}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOL_DIR=""
for candidate in "${SCRIPT_DIR}/patches" "${SCRIPT_DIR}" "/solution/patches" "/solution"; do
  if [ -f "${candidate}/ingest/segment_attach_reader.go" ]; then
    SOL_DIR="${candidate}"
    break
  fi
done
if [ -z "${SOL_DIR}" ]; then
  echo "oracle: golden patches not found" >&2
  exit 1
fi
cd "${APP_ROOT}"
cp -f "${SOL_DIR}/ingest/segment_attach_reader.go" internal/ingest/segment_attach_reader.go
cp -f "${SOL_DIR}/normalize/stat_tombstone_coalesce.go" internal/normalize/stat_tombstone_coalesce.go
cp -f "${SOL_DIR}/staging/catalog_watermark.go" internal/staging/catalog_watermark.go
cp -f "${SOL_DIR}/export/atlas_seal.go" internal/export/atlas_seal.go
cp -f "${SOL_DIR}/state/resume_attach_gate.go" internal/state/resume_attach_gate.go
go build -o /usr/local/bin/duckcatalog ./cmd/duckcatalog
duckcatalog attach --batches /app/fixtures/attach/basic_attach.jsonl --atlas /app/state/catalog-watermark-atlas.json
duckcatalog seal --atlas /app/state/catalog-watermark-atlas.json --output /app/output/sealed-attach-manifest.json
echo "oracle smoke ok"
"""

TEST_SH = """#!/usr/bin/env bash
set -uo pipefail
export PATH="/usr/local/bin:/opt/verifier-venv/bin:${PATH}"
export VERIFIER_SEED="${VERIFIER_SEED:-duckcatalog-seed-23}"
export TB3_FIXTURES_DIR="${TB3_FIXTURES_DIR:-/opt/verifier-fixtures/attach}"
TEST_DIR="${TEST_DIR:-/tests}"
mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
printf '{"version":"1.0.0","results":[]}\\n' > /logs/verifier/ctrf.json
cd /app || { echo 0 > /logs/verifier/reward.txt; exit 0; }
go build -o /usr/local/bin/duckcatalog ./cmd/duckcatalog || { echo 0 > /logs/verifier/reward.txt; exit 1; }
set +e
bash /app/scripts/reset-state.sh
/opt/verifier-venv/bin/python -m pytest -o cache_dir=/tmp/pytest_cache --ctrf /logs/verifier/ctrf.json "${TEST_DIR}/test_outputs.py" -rA
if [ $? -eq 0 ]; then echo 1 > /logs/verifier/reward.txt; else echo 0 > /logs/verifier/reward.txt; fi
"""


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def docs() -> None:
    write(ENV / "docs" / "attach-batch-schema.md", "# Attach batch schema\n\nJSONL rows include catalog_id, table_name, segment_uuid, file_offset, attach_seq, generation, column_name, logical_type, type_width, stat_value, is_deleted, checkpoint_gen.\n")
    write(ENV / "docs" / "stat-tombstone-coalesce.md", "# Stat tombstone coalesce\n\nCoalesce key is catalog_id+table_name+column_name+logical_type+type_width. Winner: higher generation, then attach_seq, then segment_uuid lex.\n")
    write(ENV / "docs" / "catalog-watermark-schema.md", "# Catalog watermark atlas\n\nSchema version 2. Watermarks track checkpoint_gen and max_generation per catalog/table. Empty attach batch must not clear watermarks.\n")
    write(ENV / "docs" / "sealed-manifest-schema.md", "# Sealed manifest\n\nEntry SHA256 includes logical_type and type_width bits. atlas_root_sha256 chains entry hashes.\n")
    write(ENV / "docs" / "cli-surface.md", "# CLI\n\nduckcatalog attach --batches PATH --atlas PATH [--resume PATH]\nduckcatalog seal --atlas PATH --output PATH\n")
    write(ENV / "docs" / "fixture-catalog.md", "# Fixtures\n\nBundled under /app/fixtures/attach/.\n")
    write(ENV / "docs" / "module-api.md", "# Modules\n\n| Path | Role |\n| ingest/segment_attach_reader.go | JSONL ingest ordering |\n| normalize/stat_tombstone_coalesce.go | Stat coalesce |\n| staging/catalog_watermark.go | Atlas persistence |\n| export/atlas_seal.go | Manifest seal |\n| state/resume_attach_gate.go | Resume filter |\n| schema/legacy/type_width_resolver.go | Decoy off hot path |\n")


def main() -> None:
    if TASK.exists():
        shutil.rmtree(TASK)
    write(TASK / "instruction.md", INSTRUCTION)
    write(TASK / "task.toml", TASK_TOML)
    write(ENV / "go.mod", GO_MOD)
    write(ENV / "cmd" / "duckcatalog" / "main.go", MAIN_GO)
    write(ENV / "internal" / "model" / "model.go", MODEL_GO)
    write(ENV / "internal" / "util" / "util.go", UTIL_GO)
    write(ENV / "internal" / "ingest" / "segment_attach_reader.go", INGEST_BROKEN)
    write(ENV / "internal" / "normalize" / "stat_tombstone_coalesce.go", NORMALIZE_BROKEN)
    write(ENV / "internal" / "staging" / "catalog_watermark.go", STAGING_BROKEN)
    write(ENV / "internal" / "export" / "atlas_seal.go", EXPORT_BROKEN)
    write(ENV / "internal" / "state" / "resume_attach_gate.go", RESUME_BROKEN)
    write(ENV / "internal" / "schema" / "legacy" / "type_width_resolver.go", DECOY)
    docs()
    write(ENV / "scripts" / "reset-state.sh", RESET_SH)
    write(ENV / "tools" / "build_fixtures.py", BUILD_FIXTURES)
    write(ENV / "tools" / "build_hidden_fixtures.py", BUILD_HIDDEN)
    write(ENV / "Dockerfile", DOCKERFILE)

    # patches
    patch_base = TASK / "solution" / "patches"
    write(patch_base / "ingest" / "segment_attach_reader.go", INGEST_GOLDEN)
    write(patch_base / "normalize" / "stat_tombstone_coalesce.go", NORMALIZE_GOLDEN)
    write(patch_base / "staging" / "catalog_watermark.go", STAGING_GOLDEN)
    write(patch_base / "export" / "atlas_seal.go", EXPORT_GOLDEN)
    write(patch_base / "state" / "resume_attach_gate.go", RESUME_GOLDEN)
    write(TASK / "solution" / "solve.sh", SOLVE_SH)
    write(TASK / "tests" / "test.sh", TEST_SH)

    tests_patch = TASK / "tests" / "patches"
    for sub in ("ingest", "normalize", "staging", "export", "state"):
        for f in (patch_base / sub).glob("*.go"):
            write(tests_patch / sub / f.name, f.read_text(encoding="utf-8"))

    # broken_src mirror
    broken = TASK / "tests" / "broken_src"
    shutil.copytree(ENV / "internal", broken / "internal", dirs_exist_ok=True)
    shutil.copytree(ENV / "cmd", broken / "cmd", dirs_exist_ok=True)

    print(f"Bootstrapped {TASK}")


if __name__ == "__main__":
    main()
