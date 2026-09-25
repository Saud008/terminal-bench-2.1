package lineagewalk

import "github.com/terminus/vaultaud/internal/model"

// Classification is the lineage result for one renewal event.
type Classification struct {
	LineageRoot     string
	LineageDepth    int
	IsOrphan        bool
	DelegatedParent string
	Ancestors       []string
}

// BuildLatest maps each token_id to its highest renewal_seq event.
func BuildLatest(events []model.RenewalEvent) map[string]model.RenewalEvent {
	best := map[string]model.RenewalEvent{}
	for _, ev := range events {
		prev, ok := best[ev.TokenID]
		if !ok || ev.RenewalSeq > prev.RenewalSeq {
			best[ev.TokenID] = ev
		}
	}
	return best
}

// BuildOrigin maps each token_id to its lowest renewal_seq event.
func BuildOrigin(events []model.RenewalEvent) map[string]model.RenewalEvent {
	best := map[string]model.RenewalEvent{}
	for _, ev := range events {
		prev, ok := best[ev.TokenID]
		if !ok || ev.RenewalSeq < prev.RenewalSeq {
			best[ev.TokenID] = ev
		}
	}
	return best
}

// Resolve walks parent_id without severing on orphan and without detecting cycles.
func Resolve(ev model.RenewalEvent, latest map[string]model.RenewalEvent) Classification {
	parent := ev.ParentID
	if parent == "" {
		return Classification{
			LineageRoot:  ev.TokenID,
			LineageDepth: 0,
			IsOrphan:     ev.Orphan,
		}
	}
	if _, ok := latest[parent]; !ok {
		return Classification{
			LineageRoot:  ev.TokenID,
			LineageDepth: 0,
			IsOrphan:     true,
		}
	}
	ancestors := []string{}
	cur := parent
	depth := 0
	for hops := 0; hops < 64; hops++ {
		row, ok := latest[cur]
		if !ok {
			return Classification{
				LineageRoot:  ev.TokenID,
				LineageDepth: depth,
				IsOrphan:     true,
				Ancestors:    ancestors,
			}
		}
		ancestors = append(ancestors, cur)
		depth++
		if row.ParentID == "" {
			return Classification{
				LineageRoot:     cur,
				LineageDepth:    depth,
				IsOrphan:        ev.Orphan,
				DelegatedParent: parent,
				Ancestors:       ancestors,
			}
		}
		cur = row.ParentID
	}
	return Classification{
		LineageRoot:     parent,
		LineageDepth:    depth,
		IsOrphan:        ev.Orphan,
		DelegatedParent: parent,
		Ancestors:       ancestors,
	}
}
