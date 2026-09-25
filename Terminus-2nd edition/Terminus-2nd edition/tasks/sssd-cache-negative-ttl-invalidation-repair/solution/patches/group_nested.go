package group

import (
	"github.com/terminus/sssdcache/internal/cache"
	"github.com/terminus/sssdcache/internal/model"
)

func AddMember(state *model.CacheState, group, member string, nested bool, stats *model.Stats) {
	if state.Groups[group] == nil {
		state.Groups[group] = map[string]bool{}
	}
	if state.Groups[group][member] {
		return
	}
	state.Groups[group][member] = true
	stats.GroupAddMember++
	InvalidateGroupMembers(state, group, nested, stats)
}

func InvalidateGroupMembers(state *model.CacheState, group string, nested bool, stats *model.Stats) {
	members, ok := state.Groups[group]
	if !ok {
		return
	}
	users := map[string]bool{}
	if nested {
		collectUsers(state, group, users)
	} else {
		for member := range members {
			users[member] = true
		}
	}
	for user := range users {
		cache.RemovePrincipal(state, state.DomainSuffix, user)
		stats.GroupInvalidations++
	}
}

func collectUsers(state *model.CacheState, group string, out map[string]bool) {
	members := state.Groups[group]
	for member := range members {
		if _, isGroup := state.Groups[member]; isGroup {
			collectUsers(state, member, out)
			continue
		}
		out[member] = true
	}
}
