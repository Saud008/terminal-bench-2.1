package closure

import (
	"strings"
	"sync"

	"github.com/example/spicedb-relation-watch/internal/store"
)

// Cache stores transitive subject expansion results.
type Cache struct {
	mu      sync.RWMutex
	entries map[string]bool
	store   *store.Store
}

// New builds a closure cache backed by store reads.
func New(st *store.Store, _ int) *Cache {
	return &Cache{
		entries: make(map[string]bool),
		store:   st,
	}
}

func cacheKey(revision int64, ns, obj, rel, subj string) string {
	return strings.Join([]string{
		itoa(revision), ns, obj, rel, subj,
	}, "|")
}

func itoa(v int64) string {
	if v == 0 {
		return "0"
	}
	neg := v < 0
	if neg {
		v = -v
	}
	var buf [20]byte
	i := len(buf)
	for v > 0 {
		i--
		buf[i] = byte('0' + v%10)
		v /= 10
	}
	if neg {
		i--
		buf[i] = '-'
	}
	return string(buf[i:])
}

// HasTransitivePermission checks subject via direct or group-member expansion.
func (c *Cache) HasTransitivePermission(revision int64, ns, obj, rel, subj string) (bool, error) {
	key := cacheKey(revision, ns, obj, rel, subj)
	c.mu.RLock()
	if v, ok := c.entries[key]; ok {
		c.mu.RUnlock()
		return v, nil
	}
	c.mu.RUnlock()

	ok, err := c.compute(revision, ns, obj, rel, subj)
	if err != nil {
		return false, err
	}
	c.mu.Lock()
	c.entries[key] = ok
	c.mu.Unlock()
	return ok, nil
}

func (c *Cache) compute(revision int64, ns, obj, rel, subj string) (bool, error) {
	exists, _, err := c.store.DirectTupleExists(revision, ns, obj, rel, subj)
	if err != nil {
		return false, err
	}
	if exists {
		return true, nil
	}
	// Transitive: object#relation@group:eng#member + group:eng#member@user:alice
	rows, err := c.store.ActiveTuplesAtRevision(revision)
	if err != nil {
		return false, err
	}
	for _, t := range rows {
		if t.Namespace != ns || t.Object != obj || t.Relation != rel {
			continue
		}
		if !strings.Contains(t.Subject, "#") {
			continue
		}
		parts := strings.SplitN(t.Subject, "#", 2)
		if len(parts) != 2 {
			continue
		}
		groupRef := parts[0]
		viaRel := parts[1]
		memberExists, _, err := c.store.DirectTupleExists(revision, ns, groupRef, viaRel, subj)
		if err != nil {
			return false, err
		}
		if memberExists {
			return true, nil
		}
	}
	return false, nil
}

// InvalidateNamespacePrefix should drop cached entries for namespaces under prefix.
func (c *Cache) InvalidateNamespacePrefix(_ string) {
}
