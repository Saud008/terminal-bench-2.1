package runchain

import (
	"encoding/json"
	"os"
	"path/filepath"

	"github.com/terminus/qqraftctl/internal/walcommit"
	"github.com/terminus/qqraftctl/internal/logparse"
	"github.com/terminus/qqraftctl/internal/votercfg"
	"github.com/terminus/qqraftctl/internal/model"
	"github.com/terminus/qqraftctl/internal/ocfcore"
	"github.com/terminus/qqraftctl/internal/bundleclip"
	"github.com/terminus/qqraftctl/internal/workpad"
)

func parseFlags(args []string) (cluster, scenario, fixtureDir string, rest []string) {
	fixtureDir = "/app/fixtures"
	if v := os.Getenv("TB3_FIXTURE_DIR"); v != "" {
		fixtureDir = v
	}
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--cluster":
			i++
			cluster = args[i]
		case "--scenario":
			i++
			scenario = args[i]
		case "--fixture-dir":
			i++
			fixtureDir = args[i]
		default:
			rest = append(rest, args[i])
		}
	}
	return cluster, scenario, fixtureDir, rest
}

func scenarioDir(fixtureDir, scenario string) string {
	return filepath.Join(fixtureDir, scenario)
}

func ReplayLog(args []string) error {
	cluster, scenario, fixtureDir, _ := parseFlags(args)
	entries, err := logparse.ReadClusterLogs(scenarioDir(fixtureDir, scenario))
	if err != nil {
		return err
	}
	res := ocfcore.Replay(cluster, entries, 0, ocfcore.ReplayBaseline{})
	return workpad.Write(workpad.DefaultPath, res.Staging)
}

func MergeSnapshot(args []string) error {
	cluster, scenario, fixtureDir, _ := parseFlags(args)
	dir := scenarioDir(fixtureDir, scenario)
	snapPath := filepath.Join(dir, "snapshot.json")
	raw, err := os.ReadFile(snapPath)
	if err != nil {
		return err
	}
	var snap model.Snapshot
	if err := json.Unmarshal(raw, &snap); err != nil {
		return err
	}
	entries, err := logparse.ReadClusterLogs(dir)
	if err != nil {
		return err
	}
	tail := bundleclip.FilterAfterSnapshot(entries, snap)
	qs, mem, commitIdx := bundleclip.LoadBaseline(snap)
	res := ocfcore.Replay(cluster, tail, snap.LastIncludedIndex, ocfcore.ReplayBaseline{})
	for k, v := range qs {
		if _, ok := res.Staging.QueueStates[k]; !ok {
			res.Staging.QueueStates[k] = v
		}
	}
	if len(res.Staging.Membership) == 0 {
		res.Staging.Membership = mem
	}
	if res.Staging.CommitIndex < commitIdx {
		res.Staging.CommitIndex = commitIdx
	}
	return workpad.Write(workpad.DefaultPath, res.Staging)
}

func AuditMembership(args []string) error {
	cluster, scenario, _, _ := parseFlags(args)
	return votercfg.WriteAudit(cluster, scenario)
}

func ExportCommitted(args []string) error {
	_, _, _, _ = parseFlags(args)
	ledgerPath := "/app/output/committed-queue-state.jsonl"
	sealPath := "/app/output/quorum-ledger-seal.json"
	st, err := workpad.Read(workpad.DefaultPath)
	if err != nil {
		return err
	}
	st.RaftSeal = workpad.ComputeRaftSeal(st)
	return walcommit.ExportLedger(st, ledgerPath, sealPath)
}
