package cache

import (
	"encoding/hex"
	"hash/fnv"

	"vtgatesim/internal/model"
)

type Store struct {
	entries []model.CacheEntry
}

func NewStore(seed []model.CacheEntry) *Store {
	cp := make([]model.CacheEntry, len(seed))
	copy(cp, seed)
	return &Store{entries: cp}
}

func (s *Store) Entries() []model.CacheEntry {
	out := make([]model.CacheEntry, len(s.entries))
	copy(out, s.entries)
	return out
}

func cacheKeyHash(vtype, key string) string {
	h := fnv.New64a()
	_, _ = h.Write([]byte(key))
	return hex.EncodeToString(h.Sum(nil))
}

func (s *Store) Lookup(vtype, key string, generation int) (model.CacheEntry, bool) {
	want := cacheKeyHash(vtype, key)
	for _, e := range s.entries {
		if e.KeyHex == want {
			return e, true
		}
	}
	return model.CacheEntry{}, false
}

func (s *Store) Put(vtype, key, shard string, generation int) {
	want := cacheKeyHash(vtype, key)
	for i := range s.entries {
		if s.entries[i].KeyHex == want {
			s.entries[i].Shard = shard
			s.entries[i].Generation = generation
			return
		}
	}
	s.entries = append(s.entries, model.CacheEntry{
		VindexName: vtype,
		KeyHex:     want,
		Shard:      shard,
		Generation: generation,
	})
}

func (s *Store) Coalesce(incoming []model.CacheEntry, generation int) []model.CacheEntry {
	merged := append([]model.CacheEntry{}, s.entries...)
	merged = append(merged, incoming...)
	s.entries = merged
	return merged
}

func (s *Store) Flush() {
	s.entries = nil
}
