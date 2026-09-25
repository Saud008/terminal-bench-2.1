package pwcore

import "sort"

func InheritFilters(inv Inventory, peer Peer) []Filter {
	var group []Filter
	for _, g := range inv.PeerGroups {
		if g.GroupID == peer.GroupID {
			group = append(group, g.Filters...)
			break
		}
	}
	out := append(append([]Filter{}, group...), peer.Filters...)
	sort.Slice(out, func(i, j int) bool {
		if out[i].Priority != out[j].Priority {
			return out[i].Priority > out[j].Priority
		}
		return out[i].FilterID < out[j].FilterID
	})
	return out
}
