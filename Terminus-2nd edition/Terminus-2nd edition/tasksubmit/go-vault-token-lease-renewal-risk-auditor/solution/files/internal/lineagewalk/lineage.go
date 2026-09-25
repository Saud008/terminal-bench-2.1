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

func effectiveParent(ev model.RenewalEvent) string {
	if ev.Orphan {
		return ""
	}
	return ev.ParentID
}

// Resolve classifies one renewal against the latest-renewal corpus.
func Resolve(ev model.RenewalEvent, latest map[string]model.RenewalEvent) Classification {
	parent := effectiveParent(ev)
	if parent == "" {
		return Classification{
			LineageRoot:  ev.TokenID,
			LineageDepth: 0,
			IsOrphan:     ev.Orphan,
		}
	}
	if _, ok := latest[parent]; !ok {
		return Classification{
			LineageRoot:  model.OrphanPrefix + ev.TokenID,
			LineageDepth: 0,
			IsOrphan:     true,
		}
	}

	visited := map[string]bool{ev.TokenID: true}
	ancestors := []string{}
	cur := parent
	depth := 0
	for {
		if visited[cur] {
			smallest := ev.TokenID
			for id := range visited {
				if id < smallest {
					smallest = id
				}
			}
			return Classification{
				LineageRoot:  model.CyclePrefix + smallest,
				LineageDepth: model.CycleDepth,
				IsOrphan:     ev.Orphan,
				Ancestors:    ancestors,
			}
		}
		row, ok := latest[cur]
		if !ok {
			return Classification{
				LineageRoot:  model.OrphanPrefix + ev.TokenID,
				LineageDepth: 0,
				IsOrphan:     true,
				Ancestors:    ancestors,
			}
		}
		visited[cur] = true
		ancestors = append(ancestors, cur)
		depth++
		next := effectiveParent(row)
		if next == "" {
			return Classification{
				LineageRoot:     cur,
				LineageDepth:    depth,
				IsOrphan:        ev.Orphan,
				DelegatedParent: parent,
				Ancestors:       ancestors,
			}
		}
		cur = next
	}
}
