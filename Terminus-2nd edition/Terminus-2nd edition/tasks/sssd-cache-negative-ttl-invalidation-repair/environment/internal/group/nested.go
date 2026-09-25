package group

import (
	"github.com/terminus/sssdcache/internal/cache"
	"github.com/terminus/sssdcache/internal/model"
)

func AddMember(state *model.CacheState, group, member string, stats *model.Stats) {
	if state.Groups[group] == nil {
		state.Groups[group] = map[string]bool{}
	}
	if state.Groups[group][member] {
		return
	}
	state.Groups[group][member] = true
	stats.GroupAddMember++
	InvalidateGroupMembers(state, group, stats)
}

// InvalidateGroupMembers removes cache rows for users affected by group change.
func InvalidateGroupMembers(state *model.CacheState, group string, stats *model.Stats) {
	members, ok := state.Groups[group]
	if !ok {
		return
	}
	for member := range members {
		if nested, isGroup := state.Groups[member]; isGroup && len(nested) > 0 {
			continue
		}
		cache.InvalidatePrincipal(state, state.DomainSuffix, member, stats)
		stats.GroupInvalidations++
	}
}
