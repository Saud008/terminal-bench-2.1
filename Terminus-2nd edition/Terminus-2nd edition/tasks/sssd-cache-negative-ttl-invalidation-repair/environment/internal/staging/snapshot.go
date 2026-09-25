package staging

import (
	"encoding/json"
	"os"
	"sort"

	"github.com/terminus/sssdcache/internal/model"
)

const DefaultPath = "/app/state/sssd-cache-snapshot.json"

func Write(path string, state *model.CacheState, stats model.Stats) error {
	snap := Build(state, stats)
	raw, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	raw = append(raw, '\n')
	return os.WriteFile(path, raw, 0o644)
}

func Read(path string) (model.Snapshot, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.Snapshot{}, err
	}
	var snap model.Snapshot
	if err := json.Unmarshal(raw, &snap); err != nil {
		return model.Snapshot{}, err
	}
	return snap, nil
}

func Build(state *model.CacheState, stats model.Stats) model.Snapshot {
	return model.Snapshot{
		SnapshotVersion: 1,
		DomainSuffix:    state.DomainSuffix,
		EvaluatedAtMS:   state.LastTS,
		Negatives:       exportNegatives(state),
		Positives:       exportPositives(state),
		Groups:          exportGroups(state),
		Stats:           stats,
	}
}

func exportNegatives(state *model.CacheState) []model.NegativeExport {
	keys := make([]string, 0, len(state.Negatives))
	for k := range state.Negatives {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	out := make([]model.NegativeExport, 0, len(keys))
	for _, k := range keys {
		n := state.Negatives[k]
		out = append(out, model.NegativeExport{
			Domain:    n.Domain,
			Name:      n.Name,
			MissTS:    n.MissTS,
			ExpiresAt: n.ExpiresAt,
		})
	}
	return out
}

func exportPositives(state *model.CacheState) []model.PositiveExport {
	keys := make([]string, 0, len(state.Positives))
	for k := range state.Positives {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	out := make([]model.PositiveExport, 0, len(keys))
	for _, k := range keys {
		meta := state.PrincipalMeta[k]
		out = append(out, model.PositiveExport{
			Domain: meta.Domain,
			Name:   meta.Name,
			Value:  state.Positives[k],
		})
	}
	return out
}

func exportGroups(state *model.CacheState) []model.GroupExport {
	names := make([]string, 0, len(state.Groups))
	for g := range state.Groups {
		names = append(names, g)
	}
	sort.Strings(names)
	out := make([]model.GroupExport, 0, len(names))
	for _, g := range names {
		members := state.Groups[g]
		memberNames := make([]string, 0, len(members))
		for m := range members {
			memberNames = append(memberNames, m)
		}
		sort.Strings(memberNames)
		out = append(out, model.GroupExport{Group: g, Members: memberNames})
	}
	return out
}
