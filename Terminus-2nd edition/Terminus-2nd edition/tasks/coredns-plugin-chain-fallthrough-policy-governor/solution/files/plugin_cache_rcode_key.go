package plugins

import (
	"sync"
	"time"

	"github.com/miekg/dns"
	"github.com/terminus/dnsplugd/internal/model"
)

type cacheEntry struct {
	msg   *dns.Msg
	until time.Time
}

type Cache struct {
	ttl   int
	mu    sync.Mutex
	store map[string]cacheEntry
}

var sharedCaches sync.Map

func NewCache(ttl int) *Cache {
	if ttl <= 0 {
		ttl = 30
	}
	if v, ok := sharedCaches.Load(ttl); ok {
		return v.(*Cache)
	}
	c := &Cache{ttl: ttl, store: map[string]cacheEntry{}}
	actual, _ := sharedCaches.LoadOrStore(ttl, c)
	return actual.(*Cache)
}

func (c *Cache) Name() string { return "cache" }

func cacheKey(ctx *model.QueryCtx) string {
	return ctx.Qname + "|" + dns.TypeToString[ctx.Qtype]
}

func (c *Cache) Serve(ctx *model.QueryCtx) (bool, error) {
	key := cacheKey(ctx)
	c.mu.Lock()
	ent, ok := c.store[key]
	c.mu.Unlock()
	if ok && time.Now().Before(ent.until) {
		ctx.Msg = ent.msg.Copy()
		ctx.Msg.Id = ctx.Req.Id
		ctx.Handled = true
		ctx.StopChain = true
		return false, nil
	}
	return true, nil
}

func (c *Cache) Store(ctx *model.QueryCtx) {
	if ctx.Msg == nil {
		return
	}
	key := cacheKey(ctx)
	c.mu.Lock()
	c.store[key] = cacheEntry{msg: ctx.Msg.Copy(), until: time.Now().Add(time.Duration(c.ttl) * time.Second)}
	c.mu.Unlock()
}

var globalCache *Cache

func SetGlobalCache(c *Cache) { globalCache = c }

func StoreAfterChain(ctx *model.QueryCtx) {
	if globalCache != nil {
		globalCache.Store(ctx)
	}
}
