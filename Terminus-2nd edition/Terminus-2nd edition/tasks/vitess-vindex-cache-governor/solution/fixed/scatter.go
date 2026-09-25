package planner

import (
	"fmt"

	"vtgatesim/internal/cache"
	"vtgatesim/internal/model"
	"vtgatesim/internal/vindex"
)

type ScatterResult struct {
	OK      bool
	Failed  []string
	Partial bool
}

func RouteQuery(
	sm model.ShardMap,
	catalog map[string]model.VindexDef,
	store *cache.Store,
	q model.Query,
) (model.RouteResult, bool, error) {
	def, ok := catalog[q.Vindex]
	if !ok {
		return model.RouteResult{}, false, fmt.Errorf("unknown vindex %s", q.Vindex)
	}
	if hit, ok := store.Lookup(q.Vindex, q.Key, sm.Generation); ok {
		return model.RouteResult{
			Vindex: q.Vindex,
			Key:    q.Key,
			Shard:  hit.Shard,
			From:   "cache",
		}, true, nil
	}
	space, err := vindex.SpaceKey(def.Type, q.Key, def)
	if err != nil {
		return model.RouteResult{}, false, err
	}
	scatter := SimulateScatter(def.Type, q.Key)
	if scatter.Partial || !scatter.OK {
		store.Invalidate(q.Vindex, q.Key)
		return model.RouteResult{}, false, fmt.Errorf("scatter failed: %v", scatter.Failed)
	}
	shard := vindex.ResolveShard(space, sm)
	store.Put(q.Vindex, q.Key, shard, sm.Generation)
	return model.RouteResult{
		Vindex: q.Vindex,
		Key:    q.Key,
		Shard:  shard,
		From:   "compute",
	}, false, nil
}

func SimulateScatter(vtype, key string) ScatterResult {
	if vtype == "binary" && len(key) >= 2 && stringsHasSuffixFold(key, "ff") {
		return ScatterResult{OK: false, Failed: []string{"-80"}, Partial: true}
	}
	return ScatterResult{OK: true}
}

func stringsHasSuffixFold(s, suffix string) bool {
	if len(s) < len(suffix) {
		return false
	}
	tail := s[len(s)-len(suffix):]
	return stringsEqualFold(tail, suffix)
}

func stringsEqualFold(a, b string) bool {
	if len(a) != len(b) {
		return false
	}
	for i := 0; i < len(a); i++ {
		ca, cb := a[i], b[i]
		if ca >= 'A' && ca <= 'Z' {
			ca += 'a' - 'A'
		}
		if cb >= 'A' && cb <= 'Z' {
			cb += 'a' - 'A'
		}
		if ca != cb {
			return false
		}
	}
	return true
}
