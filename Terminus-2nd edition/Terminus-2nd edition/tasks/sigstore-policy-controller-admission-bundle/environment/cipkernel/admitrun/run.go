// Package admitrun wires the load, select/merge, evaluate, witness, and
// seal stages together for the `slsacip attest` CLI verb.
package admitrun

import (
	"fmt"

	"github.com/terminus/slsacip/cipkernel/cipcfg"
	"github.com/terminus/slsacip/cipkernel/cipemit"
	"github.com/terminus/slsacip/cipkernel/cipload"
	"github.com/terminus/slsacip/cipkernel/ciptypes"
	"github.com/terminus/slsacip/cipkernel/quorumadmit"
	"github.com/terminus/slsacip/cipkernel/sealhex"
	"github.com/terminus/slsacip/cipkernel/witnesswrite"
)

// WitnessSnapshotPath is where the witness snapshot is staged, per
// docs/trust-witness-format.md.
const WitnessSnapshotPath = "/app/state/slsacip/trust-witness.json"

// Run loads the config, trust roots, policy packs, envelopes, and pulls,
// evaluates every pull against the merged policy, stages the witness
// snapshot, seals the audit digest, and writes the admission ledger to
// outPath.
func Run(cfgPath, pullsPath, outPath string) error {
	cfg, err := cipcfg.Load(cfgPath)
	if err != nil {
		return err
	}

	roots, err := cipload.LoadTrustRoots(cfg.TrustRootsDir)
	if err != nil {
		return fmt.Errorf("load trust roots: %w", err)
	}

	envelopes, err := cipload.LoadEnvelopes(cfg.EnvelopesDir)
	if err != nil {
		return fmt.Errorf("load envelopes: %w", err)
	}

	selected := quorumadmit.SelectPacks(cfg.Seed, cfg.PolicyPacks)

	packs := make([]ciptypes.PolicyPack, 0, len(selected))
	for _, name := range selected {
		p, err := cipload.LoadPolicyPack(cfg.PoliciesRoot, name)
		if err != nil {
			return fmt.Errorf("load policy pack %s: %w", name, err)
		}
		packs = append(packs, p)
	}
	merged := quorumadmit.MergePolicies(packs)

	pulls, err := cipload.LoadPulls(pullsPath)
	if err != nil {
		return fmt.Errorf("load pulls: %w", err)
	}

	results := make([]ciptypes.PullResult, 0, len(pulls))
	for _, pull := range pulls {
		results = append(results, quorumadmit.Evaluate(pull, merged, envelopes, roots, cfg.QuorumK))
	}

	snap, err := witnesswrite.BuildAndWrite(cfg.Seed, cfg.QuorumK, selected, roots, merged, WitnessSnapshotPath)
	if err != nil {
		return fmt.Errorf("stage witness snapshot: %w", err)
	}

	report := ciptypes.Report{
		Schema:               "slsacip.attest.v1",
		Seed:                 cfg.Seed,
		QuorumK:              cfg.QuorumK,
		PolicyPacks:          selected,
		TrustFingerprint:     snap.TrustFingerprint,
		DenyFingerprint:      snap.DenyFingerprint,
		RevokeFingerprint:    snap.RevokeFingerprint,
		PredicateFingerprint: snap.PredicateFingerprint,
		BuilderFingerprint:   snap.BuilderFingerprint,
		Results:              results,
	}
	report.AuditDigest = sealhex.AuditHex(report)

	if err := cipemit.WriteReport(report, outPath); err != nil {
		return fmt.Errorf("write report: %w", err)
	}

	return nil
}
