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

func typedKeyHex(vtype, key string) string {
	h := fnv.New64a()
	_, _ = h.Write([]byte(key))
	return vtype + ":" + hex.EncodeToString(h.Sum(nil))
}

func (s *Store) Lookup(vtype, key string, generation int) (model.CacheEntry, bool) {
	want := typedKeyHex(vtype, key)
	for _, e := range s.entries {
		if e.KeyHex == want && e.Generation == generation {
			return e, true
		}
	}
	return model.CacheEntry{}, false
}

func (s *Store) Put(vtype, key, shard string, generation int) {
	want := typedKeyHex(vtype, key)
	for i := range s.entries {
		if s.entries[i].KeyHex == want {
			s.entries[i].Shard = shard
			s.entries[i].Generation = generation
			s.entries[i].VindexName = vtype
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
	filtered := make([]model.CacheEntry, 0, len(incoming))
	for _, e := range incoming {
		if e.Generation == generation {
			filtered = append(filtered, e)
		}
	}
	merged := append([]model.CacheEntry{}, s.entries...)
	for _, e := range filtered {
		merged = append(merged, e)
	}
	s.entries = merged
	return merged
}

func (s *Store) Flush() {
	s.entries = nil
}

func (s *Store) Invalidate(vtype, key string) {
	want := typedKeyHex(vtype, key)
	out := s.entries[:0]
	for _, e := range s.entries {
		if e.KeyHex != want {
			out = append(out, e)
		}
	}
	s.entries = out
}
