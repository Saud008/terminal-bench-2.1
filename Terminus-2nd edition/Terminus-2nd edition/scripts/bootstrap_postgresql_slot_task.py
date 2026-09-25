#!/usr/bin/env python3
"""Bootstrap postgresql-replication-slot-lag-ledger task tree."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT / "tasks" / "postgresql-replication-slot-lag-ledger"
ENV = TASK / "environment"
TESTS = TASK / "tests"
SOL = TASK / "solution" / "patches"

# wipe copied etcd internals
for p in [
    ENV / "internal",
    ENV / "cmd",
    ENV / "docs",
    ENV / "fixtures",
    ENV / "verifier-fixtures",
    TESTS / "verifier-golden",
    SOL,
]:
    if p.exists():
        shutil.rmtree(p)
    p.mkdir(parents=True, exist_ok=True)

(ENV / "cmd" / "slotreplay").mkdir(parents=True)
(ENV / "internal" / "lsn").mkdir(parents=True)
(ENV / "internal" / "slot").mkdir(parents=True)
(ENV / "internal" / "staging").mkdir(parents=True)
(ENV / "internal" / "ledger").mkdir(parents=True)
(ENV / "internal" / "export").mkdir(parents=True)
(ENV / "internal" / "wrap").mkdir(parents=True)
(ENV / "internal" / "parse").mkdir(parents=True)
(ENV / "internal" / "model").mkdir(parents=True)
(ENV / "internal" / "replay").mkdir(parents=True)
(ENV / "fixtures" / "slot").mkdir(parents=True)
(ENV / "fixtures" / "logs").mkdir(parents=True)
(ENV / "verifier-fixtures" / "logs").mkdir(parents=True)

GO_MOD = """module github.com/terminus/slotreplay

go 1.24
"""

MODEL_GO = r'''package model

type Config struct {
	SlotName           string `json:"slot_name"`
	Plugin             string `json:"plugin"`
	RestartLSN         string `json:"restart_lsn"`
	InitialCatalogXmin uint32 `json:"initial_catalog_xmin"`
}

type Event struct {
	Type      string `json:"type"`
	XID       uint32 `json:"xid,omitempty"`
	Xmin      uint32 `json:"xmin,omitempty"`
	LSN       string `json:"lsn,omitempty"`
	CommitLSN string `json:"commit_lsn,omitempty"`
}

type CommitRecord struct {
	XID       uint32 `json:"xid"`
	Xmin      uint32 `json:"xmin"`
	CommitLSN string `json:"commit_lsn"`
}

type Stats struct {
	Begins          int `json:"begins"`
	Commits         int `json:"commits"`
	FlushAdvances   int `json:"flush_advances"`
	RetainAdvances  int `json:"retain_advances"`
	MergeLoads      int `json:"merge_loads"`
}

type Snapshot struct {
	SnapshotVersion   int            `json:"snapshot_version"`
	Epoch             int            `json:"epoch"`
	SlotName          string         `json:"slot_name"`
	Plugin            string         `json:"plugin"`
	RestartLSN        string         `json:"restart_lsn"`
	ConfirmedFlushLSN string         `json:"confirmed_flush_lsn"`
	RetainLSN         string         `json:"retain_lsn"`
	CatalogXmin       uint32         `json:"catalog_xmin"`
	Stats             Stats          `json:"stats"`
	Commits           []CommitRecord `json:"commits"`
	LogPath           string         `json:"log_path,omitempty"`
}

type LedgerRow struct {
	XID       uint32 `json:"xid"`
	CommitLSN string `json:"commit_lsn"`
	Xmin      uint32 `json:"xmin"`
	LagBytes  int64  `json:"lag_bytes"`
}

type Ledger struct {
	ExportVersion int         `json:"export_version"`
	SlotName      string      `json:"slot_name"`
	Epoch         int         `json:"epoch"`
	TableSuffix   string      `json:"table_suffix"`
	Stats         Stats       `json:"stats"`
	Rows          []LedgerRow `json:"rows"`
}

type MutableState struct {
	Config            Config
	Epoch             int
	RestartLSN        string
	ConfirmedFlushLSN string
	RetainLSN         string
	CatalogXmin       uint32
	ActiveXIDs        map[uint32]bool
	Commits           []CommitRecord
	Stats             Stats
	LogPath           string
}
'''

PARSE_GO = r'''package parse

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/slotreplay/internal/model"
)

func LoadConfig(path string) (model.Config, error) {
	var cfg model.Config
	b, err := os.ReadFile(path)
	if err != nil {
		return cfg, err
	}
	if err := json.Unmarshal(b, &cfg); err != nil {
		return cfg, err
	}
	if cfg.RestartLSN == "" {
		cfg.RestartLSN = "0/1000000"
	}
	if cfg.InitialCatalogXmin == 0 {
		cfg.InitialCatalogXmin = 100
	}
	return cfg, nil
}

func LoadEvents(path string) ([]model.Event, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var out []model.Event
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := sc.Bytes()
		if len(line) == 0 {
			continue
		}
		var ev model.Event
		if err := json.Unmarshal(line, &ev); err != nil {
			return nil, err
		}
		out = append(out, ev)
	}
	return out, sc.Err()
}

func LoadSnapshot(path string) (model.Snapshot, error) {
	var snap model.Snapshot
	b, err := os.ReadFile(path)
	if err != nil {
		return snap, err
	}
	err = json.Unmarshal(b, &snap)
	return snap, err
}

func WriteSnapshot(path string, snap model.Snapshot) error {
	b, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	b = append(b, '\n')
	return os.WriteFile(path, b, 0o644)
}

func WriteLedger(path string, ledger model.Ledger) error {
	b, err := json.MarshalIndent(ledger, "", "  ")
	if err != nil {
		return err
	}
	b = append(b, '\n')
	return os.WriteFile(path, b, 0o644)
}

func RequireNonEmpty(field, name string) error {
	if field == "" {
		return fmt.Errorf("%s is required", name)
	}
	return nil
}
'''

GOLDEN_COMPARE = r'''package lsn

import (
	"fmt"
	"strconv"
	"strings"
)

type Value struct {
	Segment uint32
	Offset  uint32
}

func Parse(raw string) (Value, error) {
	parts := strings.Split(strings.TrimSpace(raw), "/")
	if len(parts) != 2 {
		return Value{}, fmt.Errorf("invalid lsn %q", raw)
	}
	seg, err := strconv.ParseUint(parts[0], 16, 32)
	if err != nil {
		return Value{}, err
	}
	off, err := strconv.ParseUint(parts[1], 16, 32)
	if err != nil {
		return Value{}, err
	}
	return Value{Segment: uint32(seg), Offset: uint32(off)}, nil
}

func Compare(a, b Value) int {
	if a.Segment < b.Segment {
		return -1
	}
	if a.Segment > b.Segment {
		return 1
	}
	if a.Offset < b.Offset {
		return -1
	}
	if a.Offset > b.Offset {
		return 1
	}
	return 0
}

func Less(a, b Value) bool  { return Compare(a, b) < 0 }
func LessEq(a, b Value) bool { return Compare(a, b) <= 0 }
'''

BROKEN_COMPARE = r'''package lsn

import "strings"

type Value struct {
	Segment uint32
	Offset  uint32
}

func Parse(raw string) (Value, error) {
	return Value{}, nil
}

// Broken: lexical string ordering on raw pg_lsn text.
func Compare(a, b Value) int {
	as := strings.ToLower(strings.TrimSpace(rawA))
	bs := strings.ToLower(strings.TrimSpace(rawB))
	if as < bs {
		return -1
	}
	if as > bs {
		return 1
	}
	return 0
}

var rawA, rawB string

func SetRawCompare(a, b string) {
	rawA, rawB = a, b
}

func Less(a, b Value) bool  { return Compare(a, b) < 0 }
func LessEq(a, b Value) bool { return Compare(a, b) <= 0 }
'''

# Fix broken compare to use engine-set raw strings - need better broken design
# Use broken that parses but compares string of formatted lsn

BROKEN_COMPARE = r'''package lsn

import (
	"fmt"
	"strconv"
	"strings"
)

type Value struct {
	Segment uint32
	Offset  uint32
	Raw     string
}

func Parse(raw string) (Value, error) {
	parts := strings.Split(strings.TrimSpace(raw), "/")
	if len(parts) != 2 {
		return Value{}, fmt.Errorf("invalid lsn %q", raw)
	}
	seg, err := strconv.ParseUint(parts[0], 16, 32)
	if err != nil {
		return Value{}, err
	}
	off, err := strconv.ParseUint(parts[1], 16, 32)
	if err != nil {
		return Value{}, err
	}
	return Value{Segment: uint32(seg), Offset: uint32(off), Raw: strings.ToLower(raw)}, nil
}

// Broken: lexical compare on raw text instead of segment/offset.
func Compare(a, b Value) int {
	if a.Raw < b.Raw {
		return -1
	}
	if a.Raw > b.Raw {
		return 1
	}
	return 0
}

func Less(a, b Value) bool  { return Compare(a, b) < 0 }
func LessEq(a, b Value) bool { return Compare(a, b) <= 0 }
'''

GOLDEN_HORIZON = r'''package slot

import "github.com/terminus/slotreplay/internal/model"

func OnBegin(state *model.MutableState, xid uint32) {
	if state.ActiveXIDs == nil {
		state.ActiveXIDs = map[uint32]bool{}
	}
	state.ActiveXIDs[xid] = true
	state.Stats.Begins++
}

func OnCommit(state *model.MutableState, xid, xmin uint32, commitLSN string) {
	delete(state.ActiveXIDs, xid)
	state.Commits = append(state.Commits, model.CommitRecord{
		XID: xid, Xmin: xmin, CommitLSN: commitLSN,
	})
	if xmin > 0 {
		if state.CatalogXmin == 0 || xmin < state.CatalogXmin {
			state.CatalogXmin = xmin
		}
	}
	state.Stats.Commits++
}
'''

BROKEN_HORIZON = r'''package slot

import "github.com/terminus/slotreplay/internal/model"

func OnBegin(state *model.MutableState, xid uint32) {
	if state.ActiveXIDs == nil {
		state.ActiveXIDs = map[uint32]bool{}
	}
	state.ActiveXIDs[xid] = true
	state.Stats.Begins++
}

// Broken: only raises catalog_xmin when new xmin is greater (wrong direction).
func OnCommit(state *model.MutableState, xid, xmin uint32, commitLSN string) {
	delete(state.ActiveXIDs, xid)
	state.Commits = append(state.Commits, model.CommitRecord{
		XID: xid, Xmin: xmin, CommitLSN: commitLSN,
	})
	if xmin > state.CatalogXmin {
		state.CatalogXmin = xmin
	}
	state.Stats.Commits++
}
'''

GOLDEN_ADVANCE = r'''package slot

import (
	"fmt"

	"github.com/terminus/slotreplay/internal/lsn"
	"github.com/terminus/slotreplay/internal/model"
)

func SetConfirmedFlush(state *model.MutableState, target string) error {
	val, err := lsn.Parse(target)
	if err != nil {
		return err
	}
	restart, err := lsn.Parse(state.RestartLSN)
	if err != nil {
		return err
	}
	retain, err := lsn.Parse(state.RetainLSN)
	if err != nil {
		return err
	}
	if !lsn.LessEq(restart, val) || !lsn.LessEq(val, retain) {
		return fmt.Errorf("confirmed_flush_lsn violates barrier triangle")
	}
	state.ConfirmedFlushLSN = target
	state.Stats.FlushAdvances++
	return nil
}

func SetRetain(state *model.MutableState, target string) error {
	val, err := lsn.Parse(target)
	if err != nil {
		return err
	}
	restart, err := lsn.Parse(state.RestartLSN)
	if err != nil {
		return err
	}
	confirmed, err := lsn.Parse(state.ConfirmedFlushLSN)
	if err != nil {
		return err
	}
	if !lsn.LessEq(restart, val) || !lsn.LessEq(confirmed, val) {
		return fmt.Errorf("retain_lsn violates barrier triangle")
	}
	state.RetainLSN = target
	state.Stats.RetainAdvances++
	return nil
}
'''

BROKEN_ADVANCE = r'''package slot

import (
	"github.com/terminus/slotreplay/internal/model"
)

// Broken: advances confirmed_flush without barrier triangle checks.
func SetConfirmedFlush(state *model.MutableState, target string) error {
	state.ConfirmedFlushLSN = target
	state.Stats.FlushAdvances++
	return nil
}

func SetRetain(state *model.MutableState, target string) error {
	state.RetainLSN = target
	state.Stats.RetainAdvances++
	return nil
}
'''

GOLDEN_MERGE = r'''package staging

import (
	"os"

	"github.com/terminus/slotreplay/internal/parse"
	"github.com/terminus/slotreplay/internal/model"
)

func LoadPrior(snapshotPath string, state *model.MutableState) error {
	if snapshotPath == "" {
		return nil
	}
	if _, err := os.Stat(snapshotPath); os.IsNotExist(err) {
		return nil
	}
	prior, err := parse.LoadSnapshot(snapshotPath)
	if err != nil {
		return err
	}
	state.Epoch = prior.Epoch
	state.Stats.MergeLoads++
	state.Stats.Begins += prior.Stats.Begins
	state.Stats.Commits += prior.Stats.Commits
	state.Stats.FlushAdvances += prior.Stats.FlushAdvances
	state.Stats.RetainAdvances += prior.Stats.RetainAdvances
	state.ConfirmedFlushLSN = prior.ConfirmedFlushLSN
	state.RetainLSN = prior.RetainLSN
	if prior.CatalogXmin > 0 && (state.CatalogXmin == 0 || prior.CatalogXmin < state.CatalogXmin) {
		state.CatalogXmin = prior.CatalogXmin
	}
	return nil
}

func FinalizeEpoch(state *model.MutableState) {
	state.Epoch++
}
'''

BROKEN_MERGE = r'''package staging

import "github.com/terminus/slotreplay/internal/model"

// Broken: ignores prior snapshot epoch and counters on replay reruns.
func LoadPrior(snapshotPath string, state *model.MutableState) error {
	return nil
}

func FinalizeEpoch(state *model.MutableState) {
	state.Epoch = 1
}
'''

GOLDEN_STAGING = r'''package ledger

import "github.com/terminus/slotreplay/internal/model"

func BuildSnapshot(state model.MutableState) model.Snapshot {
	commits := append([]model.CommitRecord(nil), state.Commits...)
	return model.Snapshot{
		SnapshotVersion:   1,
		Epoch:             state.Epoch,
		SlotName:          state.Config.SlotName,
		Plugin:            state.Config.Plugin,
		RestartLSN:        state.RestartLSN,
		ConfirmedFlushLSN: state.ConfirmedFlushLSN,
		RetainLSN:         state.RetainLSN,
		CatalogXmin:       state.CatalogXmin,
		Stats:             state.Stats,
		Commits:           commits,
		LogPath:           state.LogPath,
	}
}
'''

BROKEN_STAGING = r'''package ledger

import "github.com/terminus/slotreplay/internal/model"

// Broken: drops commit rows and zeros stats before staging write.
func BuildSnapshot(state model.MutableState) model.Snapshot {
	return model.Snapshot{
		SnapshotVersion:   1,
		Epoch:             state.Epoch,
		SlotName:          state.Config.SlotName,
		Plugin:            state.Config.Plugin,
		RestartLSN:        state.RestartLSN,
		ConfirmedFlushLSN: state.ConfirmedFlushLSN,
		RetainLSN:         state.RetainLSN,
		CatalogXmin:       state.CatalogXmin,
		Stats:             model.Stats{},
		Commits:           nil,
		LogPath:           state.LogPath,
	}
}
'''

GOLDEN_PUBLISH = r'''package export

import (
	"os"
	"sort"

	"github.com/terminus/slotreplay/internal/lsn"
	"github.com/terminus/slotreplay/internal/model"
)

func tableSuffix() string {
	if v := os.Getenv("VERIFIER_TABLE_SUFFIX"); v != "" {
		return v
	}
	return "default"
}

func lagBytes(retain, commit string) int64 {
	r, err1 := lsn.Parse(retain)
	c, err2 := lsn.Parse(commit)
	if err1 != nil || err2 != nil {
		return 0
	}
	if r.Segment == c.Segment {
		return int64(r.Offset) - int64(c.Offset)
	}
	return int64(r.Segment-c.Segment)*0x100000000 + int64(r.Offset) - int64(c.Offset)
}

func PublishFromSnapshot(snap model.Snapshot) model.Ledger {
	rows := make([]model.LedgerRow, 0, len(snap.Commits))
	for _, c := range snap.Commits {
		rows = append(rows, model.LedgerRow{
			XID: c.XID, CommitLSN: c.CommitLSN, Xmin: c.Xmin,
			LagBytes: lagBytes(snap.RetainLSN, c.CommitLSN),
		})
	}
	sort.Slice(rows, func(i, j int) bool {
		if rows[i].XID == rows[j].XID {
			return rows[i].CommitLSN < rows[j].CommitLSN
		}
		return rows[i].XID < rows[j].XID
	})
	return model.Ledger{
		ExportVersion: 1,
		SlotName:      snap.SlotName,
		Epoch:         snap.Epoch,
		TableSuffix:   tableSuffix(),
		Stats:         snap.Stats,
		Rows:          rows,
	}
}
'''

BROKEN_PUBLISH = r'''package export

import (
	"os"
	"sort"

	"github.com/terminus/slotreplay/internal/lsn"
	"github.com/terminus/slotreplay/internal/model"
	"github.com/terminus/slotreplay/internal/parse"
)

func tableSuffix() string {
	if v := os.Getenv("VERIFIER_TABLE_SUFFIX"); v != "" {
		return v
	}
	return "default"
}

func lagBytes(retain, commit string) int64 {
	r, _ := lsn.Parse(retain)
	c, _ := lsn.Parse(commit)
	if r.Segment == c.Segment {
		return int64(r.Offset - c.Offset)
	}
	return 0
}

// Broken: re-parses ops log during export instead of snapshot commits only.
func PublishFromSnapshot(snap model.Snapshot) model.Ledger {
	commits := snap.Commits
	if snap.LogPath != "" {
		events, err := parse.LoadEvents(snap.LogPath)
		if err == nil {
			commits = nil
			for _, ev := range events {
				if ev.Type == "commit" {
					commits = append(commits, model.CommitRecord{
						XID: ev.XID, Xmin: ev.Xmin, CommitLSN: ev.CommitLSN,
					})
				}
			}
		}
	}
	rows := make([]model.LedgerRow, 0, len(commits))
	for _, c := range commits {
		rows = append(rows, model.LedgerRow{
			XID: c.XID, CommitLSN: c.CommitLSN, Xmin: c.Xmin,
			LagBytes: lagBytes(snap.RetainLSN, c.CommitLSN),
		})
	}
	sort.Slice(rows, func(i, j int) bool {
		return cLagKey(rows[i]) < cLagKey(rows[j])
	})
	return model.Ledger{
		ExportVersion: 1,
		SlotName:      snap.SlotName,
		Epoch:         snap.Epoch,
		TableSuffix:   tableSuffix(),
		Stats:         snap.Stats,
		Rows:          rows,
	}
}

func cLagKey(r model.LedgerRow) string {
	return r.CommitLSN
}
'''

DECOY_WRAP = r'''package wrap

import "regexp"

var slotNamePattern = regexp.MustCompile(`^[a-z][a-z0-9_]{0,62}$`)

// ValidateSlotName is a legacy helper not used by replay or publish hot paths.
func ValidateSlotName(name string) bool {
	return slotNamePattern.MatchString(name)
}
'''

ENGINE_GO = r'''package replay

import (
	"fmt"

	"github.com/terminus/slotreplay/internal/ledger"
	"github.com/terminus/slotreplay/internal/model"
	"github.com/terminus/slotreplay/internal/slot"
	"github.com/terminus/slotreplay/internal/staging"
)

func Replay(cfg model.Config, events []model.Event, snapshotPath, logPath string) (model.Snapshot, error) {
	state := model.MutableState{
		Config:            cfg,
		RestartLSN:        cfg.RestartLSN,
		ConfirmedFlushLSN: cfg.RestartLSN,
		RetainLSN:         cfg.RestartLSN,
		CatalogXmin:       cfg.InitialCatalogXmin,
		ActiveXIDs:        map[uint32]bool{},
		Commits:           []model.CommitRecord{},
		LogPath:           logPath,
	}
	if err := staging.LoadPrior(snapshotPath, &state); err != nil {
		return model.Snapshot{}, err
	}

	for _, ev := range events {
		switch ev.Type {
		case "begin":
			if ev.XID == 0 {
				return model.Snapshot{}, fmt.Errorf("begin missing xid")
			}
			slot.OnBegin(&state, ev.XID)
		case "commit":
			if ev.XID == 0 || ev.CommitLSN == "" {
				return model.Snapshot{}, fmt.Errorf("commit missing fields")
			}
			slot.OnCommit(&state, ev.XID, ev.Xmin, ev.CommitLSN)
		case "set_flush":
			if err := slot.SetConfirmedFlush(&state, ev.LSN); err != nil {
				return model.Snapshot{}, err
			}
		case "set_retain":
			if err := slot.SetRetain(&state, ev.LSN); err != nil {
				return model.Snapshot{}, err
			}
		default:
			return model.Snapshot{}, fmt.Errorf("unknown event type %q", ev.Type)
		}
	}
	staging.FinalizeEpoch(&state)
	return ledger.BuildSnapshot(state), nil
}
'''

MAIN_GO = r'''package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/terminus/slotreplay/internal/export"
	"github.com/terminus/slotreplay/internal/parse"
	"github.com/terminus/slotreplay/internal/replay"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "expected subcommand replay or publish")
		os.Exit(2)
	}
	switch os.Args[1] {
	case "replay":
		runReplay(os.Args[2:])
	case "publish":
		runPublish(os.Args[2:])
	default:
		fmt.Fprintf(os.Stderr, "unknown subcommand %s\n", os.Args[1])
		os.Exit(2)
	}
}

func runReplay(args []string) {
	fs := flag.NewFlagSet("replay", flag.ContinueOnError)
	var configPath, logPath, snapshotPath string
	fs.StringVar(&configPath, "config", "", "path to slot config json")
	fs.StringVar(&logPath, "log", "", "path to decoding jsonl")
	fs.StringVar(&snapshotPath, "snapshot", "", "snapshot output path")
	if err := fs.Parse(args); err != nil {
		os.Exit(2)
	}
	if configPath == "" || logPath == "" || snapshotPath == "" {
		fmt.Fprintln(os.Stderr, "replay requires --config, --log, --snapshot")
		os.Exit(2)
	}
	cfg, err := parse.LoadConfig(configPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	events, err := parse.LoadEvents(logPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	snap, err := replay.Replay(cfg, events, snapshotPath, logPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := parse.WriteSnapshot(snapshotPath, snap); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func runPublish(args []string) {
	fs := flag.NewFlagSet("publish", flag.ContinueOnError)
	var snapshotPath, outputPath string
	fs.StringVar(&snapshotPath, "snapshot", "", "snapshot input path")
	fs.StringVar(&outputPath, "output", "", "ledger output path")
	if err := fs.Parse(args); err != nil {
		os.Exit(2)
	}
	if snapshotPath == "" || outputPath == "" {
		fmt.Fprintln(os.Stderr, "publish requires --snapshot, --output")
		os.Exit(2)
	}
	snap, err := parse.LoadSnapshot(snapshotPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	ledgerOut := export.PublishFromSnapshot(snap)
	if err := parse.WriteLedger(outputPath, ledgerOut); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
'''

# Fixtures
SLOT_CONFIG = {
    "slot_name": "replica_sub",
    "plugin": "pgoutput",
    "restart_lsn": "0/1000000",
    "initial_catalog_xmin": 100,
}

FIXTURES = {
    "basic-slot.jsonl": [
        {"type": "begin", "xid": 10, "lsn": "0/1000100"},
        {"type": "commit", "xid": 10, "xmin": 90, "commit_lsn": "0/1000200"},
        {"type": "set_retain", "lsn": "0/1000300"},
        {"type": "set_flush", "lsn": "0/1000200"},
    ],
    "xmin-out-of-order.jsonl": [
        {"type": "begin", "xid": 200, "lsn": "0/2000100"},
        {"type": "commit", "xid": 200, "xmin": 80, "commit_lsn": "0/2000200"},
        {"type": "begin", "xid": 100, "lsn": "0/2000300"},
        {"type": "commit", "xid": 100, "xmin": 50, "commit_lsn": "0/2000400"},
        {"type": "set_retain", "lsn": "0/2000500"},
        {"type": "set_flush", "lsn": "0/2000400"},
    ],
    "lsn-segment-rollover.jsonl": [
        {"type": "begin", "xid": 1, "lsn": "0/FFFFFF00"},
        {"type": "commit", "xid": 1, "xmin": 70, "commit_lsn": "0/FFFFFFF0"},
        {"type": "set_retain", "lsn": "1/00000010"},
        {"type": "set_flush", "lsn": "0/FFFFFFF0"},
    ],
    "barrier-triangle.jsonl": [
        {"type": "begin", "xid": 5, "lsn": "0/3000100"},
        {"type": "commit", "xid": 5, "xmin": 60, "commit_lsn": "0/3000200"},
        {"type": "set_retain", "lsn": "0/3000500"},
        {"type": "set_flush", "lsn": "0/3000300"},
    ],
    "multi-commit.jsonl": [
        {"type": "begin", "xid": 1, "lsn": "0/4000100"},
        {"type": "commit", "xid": 1, "xmin": 88, "commit_lsn": "0/4000200"},
        {"type": "begin", "xid": 2, "lsn": "0/4000300"},
        {"type": "commit", "xid": 2, "xmin": 77, "commit_lsn": "0/4000400"},
        {"type": "set_retain", "lsn": "0/4000600"},
        {"type": "set_flush", "lsn": "0/4000400"},
    ],
    "short-lsn-compare.jsonl": [
        {"type": "begin", "xid": 9, "lsn": "0/1000001"},
        {"type": "commit", "xid": 9, "xmin": 65, "commit_lsn": "0/1000008"},
        {"type": "set_retain", "lsn": "0/1000010"},
        {"type": "set_flush", "lsn": "0/1000002"},
    ],
}

HIDDEN_TRAP = [
    {"type": "begin", "xid": 300, "lsn": "0/5000100"},
    {"type": "commit", "xid": 300, "xmin": 95, "commit_lsn": "0/5000200"},
    {"type": "set_retain", "lsn": "0/5000600"},
    {"type": "set_flush", "lsn": "0/5000300"},
    {"type": "begin", "xid": 301, "lsn": "0/5000400"},
    {"type": "commit", "xid": 301, "xmin": 40, "commit_lsn": "0/5000500"},
]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def golden_name(module: str) -> str:
    return f"golden_{module}.go"


MODULE_MAP = {
    "compare": ENV / "internal/lsn/compare.go",
    "horizon": ENV / "internal/slot/horizon.go",
    "advance": ENV / "internal/slot/advance.go",
    "merge": ENV / "internal/staging/merge.go",
    "staging": ENV / "internal/ledger/staging.go",
    "publish": ENV / "internal/export/publish.go",
}

GOLDEN_SOURCES = {
    "compare": GOLDEN_COMPARE,
    "horizon": GOLDEN_HORIZON,
    "advance": GOLDEN_ADVANCE,
    "merge": GOLDEN_MERGE,
    "staging": GOLDEN_STAGING,
    "publish": GOLDEN_PUBLISH,
}

BROKEN_SOURCES = {
    "compare": BROKEN_COMPARE,
    "horizon": BROKEN_HORIZON,
    "advance": BROKEN_ADVANCE,
    "merge": BROKEN_MERGE,
    "staging": BROKEN_STAGING,
    "publish": BROKEN_PUBLISH,
}


def main() -> None:
    (ENV / "go.mod").write_text(GO_MOD, encoding="utf-8")
    (ENV / "internal/model/model.go").write_text(MODEL_GO, encoding="utf-8")
    (ENV / "internal/parse/load.go").write_text(PARSE_GO, encoding="utf-8")
    (ENV / "internal/replay/engine.go").write_text(ENGINE_GO, encoding="utf-8")
    (ENV / "internal/wrap/validate.go").write_text(DECOY_WRAP, encoding="utf-8")
    (ENV / "cmd/slotreplay/main.go").write_text(MAIN_GO, encoding="utf-8")

    for mod, content in BROKEN_SOURCES.items():
        MODULE_MAP[mod].write_text(content, encoding="utf-8")
    for mod, content in GOLDEN_SOURCES.items():
        (SOL / golden_name(mod)).write_text(content, encoding="utf-8")
        (TESTS / "verifier-golden" / golden_name(mod)).write_text(content, encoding="utf-8")

    (ENV / "fixtures/slot/config.json").write_text(json.dumps(SLOT_CONFIG, indent=2) + "\n", encoding="utf-8")
    for name, rows in FIXTURES.items():
        write_jsonl(ENV / "fixtures/logs" / name, rows)
    write_jsonl(ENV / "verifier-fixtures/logs/barrier-xmin-trap.jsonl", HIDDEN_TRAP)

    print("bootstrap: core Go + fixtures written")


if __name__ == "__main__":
    main()
