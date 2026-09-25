package pwcore

import "sort"

func InheritFilters(inv Inventory, peer Peer) []Filter {
	effective := map[string]Filter{}
	for _, g := range inv.PeerGroups {
		if g.GroupID == peer.GroupID {
			for _, f := range g.Filters {
				effective[f.FilterID] = f
			}
			break
		}
	}
	for _, f := range peer.Filters {
		effective[f.FilterID] = f
	}
	out := make([]Filter, 0, len(effective))
	for _, f := range effective {
		out = append(out, f)
	}
	sort.Slice(out, func(i, j int) bool {
		if out[i].Priority != out[j].Priority {
			return out[i].Priority > out[j].Priority
		}
		return out[i].FilterID < out[j].FilterID
	})
	return out
}
