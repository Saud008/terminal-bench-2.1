package orchestrator

import (
	"github.com/terminus/mpiqctl/internal/bundleload"
	"github.com/terminus/mpiqctl/internal/calendarguard"
	"github.com/terminus/mpiqctl/internal/graphbuilder"
	"github.com/terminus/mpiqctl/internal/inspectassign"
	"github.com/terminus/mpiqctl/internal/manifestemit"
	"github.com/terminus/mpiqctl/internal/districtgate"
	"github.com/terminus/mpiqctl/internal/rankengine"
	"github.com/terminus/mpiqctl/internal/slotledger"
)

func SnapshotLoad(scenario, fixtureDir string) error {
	b, err := bundleload.LoadBundle(scenario, fixtureDir)
	if err != nil {
		return err
	}
	if err := bundleload.PersistBundle(b); err != nil {
		return err
	}
	return slotledger.Append("snapshot-load", map[string]any{"scenario": scenario})
}

func CompilePolicy(scenario string) error {
	if err := bundleload.BundleLoaded(scenario); err != nil {
		return err
	}
	return graphbuilder.CompilePolicy()
}

func ApplyHolds(scenario string) error {
	if err := bundleload.BundleLoaded(scenario); err != nil {
		return err
	}
	return districtgate.ApplyHolds()
}

func FilterBlackouts(scenario string) error {
	if err := bundleload.BundleLoaded(scenario); err != nil {
		return err
	}
	return calendarguard.FilterBlackouts()
}

func ScoreQueue(scenario string) error {
	if err := bundleload.BundleLoaded(scenario); err != nil {
		return err
	}
	return rankengine.RunScoring()
}

func BindInspectors(scenario string) error {
	if err := bundleload.BundleLoaded(scenario); err != nil {
		return err
	}
	return inspectassign.RunBinding()
}

func PublishQueue(scenario, outPath string) error {
	if err := bundleload.BundleLoaded(scenario); err != nil {
		return err
	}
	return manifestemit.PublishQueue(scenario, outPath)
}
