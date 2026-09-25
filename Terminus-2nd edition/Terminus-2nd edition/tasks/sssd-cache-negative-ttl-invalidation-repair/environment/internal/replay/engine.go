package replay

import (
	"sort"

	"github.com/terminus/sssdcache/internal/cache"
	"github.com/terminus/sssdcache/internal/config"
	"github.com/terminus/sssdcache/internal/group"
	"github.com/terminus/sssdcache/internal/model"
)

// kindPriority assigns tie-break order when ts and seq are equal.
func kindPriority(kind string) int {
	switch kind {
	case "cache_del":
		return 1
	case "lookup_hit":
		return 2
	case "invalidate":
		return 3
	case "group_add_member":
		return 4
	case "cache_put":
		return 5
	case "lookup_miss":
		return 6
	default:
		return 99
	}
}

func sortOps(ops []model.Op) {
	sort.Slice(ops, func(i, j int) bool {
		a, b := ops[i], ops[j]
		if a.TS != b.TS {
			return a.TS < b.TS
		}
		if a.Seq != b.Seq {
			return a.Seq < b.Seq
		}
		return kindPriority(a.Kind) < kindPriority(b.Kind)
	})
}

func effectiveDomain(op model.Op, cfg config.Config) string {
	if op.Domain != "" {
		return op.Domain
	}
	return cfg.DomainSuffix
}

func Replay(ops []model.Op, cfg config.Config) (*model.CacheState, model.Stats) {
	state := model.NewCacheState(cfg.DomainSuffix)
	stats := model.Stats{}
	sortOps(ops)

	for _, op := range ops {
		if op.Kind == "" {
			stats.ParseErrors++
			continue
		}
		domain := effectiveDomain(op, cfg)
		if op.TS > state.LastTS {
			state.LastTS = op.TS
		}
		switch op.Kind {
		case "lookup_miss":
			cache.OnLookupMiss(state, domain, op.Name, op.TS, cfg.NegativeTTLSec, &stats)
		case "lookup_hit":
			cache.OnLookupHit(state, domain, op.Name, &stats)
		case "cache_put":
			cache.OnCachePut(state, domain, op.Name, op.Value, &stats)
		case "cache_del":
			cache.OnCacheDel(state, domain, op.Name, &stats)
		case "group_add_member":
			group.AddMember(state, op.Group, op.Member, &stats)
		case "invalidate":
			cache.InvalidatePrincipal(state, domain, op.Name, &stats)
		default:
			stats.ParseErrors++
			continue
		}
		stats.OpsApplied++
	}
	return state, stats
}
