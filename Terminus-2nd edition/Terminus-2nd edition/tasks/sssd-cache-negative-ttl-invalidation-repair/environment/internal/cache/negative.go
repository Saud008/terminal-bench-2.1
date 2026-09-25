package cache

import (
	"github.com/terminus/sssdcache/internal/model"
)

func OnLookupMiss(state *model.CacheState, domain, name string, ts int64, ttlSec int, stats *model.Stats) {
	key := CacheKey(domain, name)
	stats.LookupMiss++

	if neg, ok := state.Negatives[key]; ok && ts < neg.ExpiresAt {
		return
	}

	ttlMS := int64(ttlSec) * 1000
	state.Negatives[key] = &model.NegativeEntry{
		Domain:    domain,
		Name:      name,
		MissTS:    ts,
		ExpiresAt: ts + ttlMS,
	}
	stats.NegativeCreated++
}

func OnLookupHit(state *model.CacheState, domain, name string, stats *model.Stats) {
	key := CacheKey(domain, name)
	stats.LookupHit++
	delete(state.Negatives, key)
}

func OnCachePut(state *model.CacheState, domain, name, value string, stats *model.Stats) {
	key := CacheKey(domain, name)
	delete(state.Negatives, key)
	state.Positives[key] = value
	state.PrincipalMeta[key] = model.PrincipalMeta{Domain: domain, Name: name}
	stats.CachePut++
}

func OnCacheDel(state *model.CacheState, domain, name string, stats *model.Stats) {
	key := CacheKey(domain, name)
	delete(state.Positives, key)
	delete(state.Negatives, key)
	delete(state.PrincipalMeta, key)
	stats.CacheDel++
}

func InvalidatePrincipal(state *model.CacheState, domain, name string, stats *model.Stats) {
	RemovePrincipal(state, domain, name)
	stats.ExplicitInvalidation++
}

func RemovePrincipal(state *model.CacheState, domain, name string) {
	key := CacheKey(domain, name)
	delete(state.Positives, key)
	delete(state.Negatives, key)
	delete(state.PrincipalMeta, key)
}
