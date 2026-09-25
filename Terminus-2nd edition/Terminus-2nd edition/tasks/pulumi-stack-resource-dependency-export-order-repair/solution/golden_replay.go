package replay

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/pulumi-dep-export/internal/export"
	"github.com/terminus/pulumi-dep-export/internal/graph"
	"github.com/terminus/pulumi-dep-export/internal/ingest"
	"github.com/terminus/pulumi-dep-export/internal/validate"
)

const ledgerPath = "/app/state/dep-ledger.json"

func OrderStack(stackPath, outputPath string) error {
	snap, err := ingest.LoadSnapshot(stackPath)
	if err != nil {
		return err
	}
	if err := validate.ValidateSnapshot(snap); err != nil {
		return err
	}
	resources := graph.FlattenComponents(snap.Resources)
	adj := graph.BuildAdjacency(resources)
	if err := graph.WriteLedger(ledgerPath, snap.Stack, resources, adj); err != nil {
		return err
	}
	report := export.BuildReport(snap, ledgerPath)
	raw, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return err
	}
	if err := os.WriteFile(outputPath, append(raw, '\n'), 0o644); err != nil {
		return err
	}
	return nil
}

func OrderStackCLI(stackPath, outputPath string) int {
	if _, err := os.Stat(stackPath); err != nil {
		fmt.Fprintf(os.Stderr, "stack not found: %s\n", stackPath)
		return 2
	}
	if err := OrderStack(stackPath, outputPath); err != nil {
		fmt.Fprintf(os.Stderr, "order failed: %v\n", err)
		return 3
	}
	return 0
}
