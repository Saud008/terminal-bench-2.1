// Package authzkernel hosts the offline access-decision attestation pipeline:
// policy snapshot staging, domain-scoped rule evaluation, deny-overrides-allow
// effect, and witness-bound audit_digest export per /app/docs/trust-admission-workflow.md.
package authzkernel

import (
	"path/filepath"
	"sort"

	"github.com/terminus/casctl/internal/config"
	"github.com/terminus/casctl/internal/export"
	"github.com/terminus/casctl/internal/model"
	"github.com/terminus/casctl/internal/parse"
)

func Run(cfgPath, requestsPath, outPath, fixturesRoot string) (int, error) {
	cfg, err := config.Load(cfgPath)
	if err != nil {
		return 2, err
	}
	modelPath := filepath.Join(fixturesRoot, "models", cfg.Model+".conf")
	modelName, err := parse.LoadModelName(modelPath)
	if err != nil {
		return 2, err
	}
	eng, err := LoadEngine(filepath.Join(fixturesRoot, "policies"), cfg.Seed, cfg.Bundles)
	if err != nil {
		return 2, err
	}
	if err := WritePolicySnapshot(PolicySnapshotPath, cfg.Seed, cfg.Bundles, eng); err != nil {
		return 2, err
	}
	reqs, err := parse.LoadRequests(requestsPath)
	if err != nil {
		return 2, err
	}

	ordered := append([]model.Policy(nil), eng.Policies...)
	sort.Slice(ordered, func(i, j int) bool {
		return ordered[i].Priority > ordered[j].Priority
	})

	stats := model.Stats{
		PoliciesLoaded:  len(eng.Policies),
		GroupingsLoaded: len(eng.Groupings),
		Requests:        len(reqs),
	}
	results := make([]model.Result, 0, len(reqs))

	for _, req := range reqs {
		scope := DomainPolicies(ordered, req.Dom)
		var matches []model.Policy
		seenPriority := map[int]bool{}
		for _, pol := range scope {
			if !MatchRequest(req, pol, eng.Groupings) {
				continue
			}
			if seenPriority[pol.Priority] {
				continue
			}
			seenPriority[pol.Priority] = true
			matches = append(matches, pol)
		}
		decision := Decide(matches)
		if decision == "allow" {
			stats.Allows++
		} else {
			stats.Denies++
		}
		results = append(results, model.Result{
			Sub:        req.Sub,
			Dom:        req.Dom,
			Obj:        req.Obj,
			Act:        req.Act,
			Decision:   decision,
			MatchCount: len(matches),
		})
	}

	rep := model.Report{
		Model:   modelName,
		Bundles: SelectBundles(cfg.Seed, cfg.Bundles),
		Results: results,
		Stats:   stats,
	}
	digest, err := ComputeAuditDigest(rep, PolicySnapshotPath)
	if err != nil {
		return 2, err
	}
	rep.AuditDigest = digest
	if err := export.Write(outPath, rep); err != nil {
		return 2, err
	}
	return 0, nil
}
