package replay

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/temporal-signal-replay/internal/dedup"
	"github.com/terminus/temporal-signal-replay/internal/export"
	"github.com/terminus/temporal-signal-replay/internal/handler"
	"github.com/terminus/temporal-signal-replay/internal/heartbeat"
	"github.com/terminus/temporal-signal-replay/internal/model"
	"github.com/terminus/temporal-signal-replay/internal/parse"
	"github.com/terminus/temporal-signal-replay/internal/router"
	"github.com/terminus/temporal-signal-replay/internal/staging"
	"github.com/terminus/temporal-signal-replay/internal/version"
)

func ExportScenario(scenarioPath, outputPath string) error {
	sc, err := parse.LoadScenario(scenarioPath)
	if err != nil {
		return err
	}
	routed := router.ResolveVersion(sc)
	snap := model.Snapshot{
		WorkflowID:        sc.WorkflowID,
		RoutedVersion:     routed,
		AckedSignals:      []string{},
		DedupSeen:         []string{},
		HeartbeatOffset:   []int64{},
	}
	for _, sig := range sc.Signals {
		if !version.GateOpen(routed, sig.TargetVersion) {
			continue
		}
		if !dedup.RegisterSignal(&snap, sig.SignalID) {
			snap.DedupSkipped++
			continue
		}
		if err := handler.ProcessSignal(sc, &snap, sig, routed); err != nil {
			return err
		}
	}
	for _, beat := range sc.Activities {
		heartbeat.RecordBeat(&snap, beat)
	}
	if err := staging.WriteSnapshot(snap); err != nil {
		return err
	}
	report, err := export.BuildReport(sc)
	if err != nil {
		return err
	}
	raw, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return err
	}
	if err := os.WriteFile(outputPath, append(raw, '\n'), 0o644); err != nil {
		return err
	}
	return nil
}

func ExportCLI(scenarioPath, outputPath string) int {
	if _, err := os.Stat(scenarioPath); err != nil {
		fmt.Fprintf(os.Stderr, "scenario not found: %s\n", scenarioPath)
		return 2
	}
	if err := ExportScenario(scenarioPath, outputPath); err != nil {
		fmt.Fprintf(os.Stderr, "export failed: %v\n", err)
		return 3
	}
	return 0
}
