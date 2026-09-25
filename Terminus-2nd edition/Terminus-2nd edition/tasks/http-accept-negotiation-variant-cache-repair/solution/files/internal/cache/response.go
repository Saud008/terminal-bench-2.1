package cache

import (
	"fmt"
	"sync"

	"github.com/terminus/variantgate/internal/model"
)

type CachedResponse struct {
	Status      int
	ContentType string
	Vary        string
	Body        []byte
}

type ResponseCache struct {
	mu     sync.Mutex
	data   map[string]CachedResponse
	hits   int
	misses int
}

func New() *ResponseCache {
	return &ResponseCache{data: map[string]CachedResponse{}}
}

func (c *ResponseCache) Stats() model.CacheStats {
	c.mu.Lock()
	defer c.mu.Unlock()
	return model.CacheStats{Hits: c.hits, Misses: c.misses}
}

func (c *ResponseCache) Reset() {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.data = map[string]CachedResponse{}
	c.hits = 0
	c.misses = 0
}

func (c *ResponseCache) cacheKey(path string, in model.NegotiationInput) string {
	return fmt.Sprintf("%s|%s|%s|%s",
		path,
		in.Accept,
		in.AcceptLanguage,
		in.AcceptCharset,
	)
}

func (c *ResponseCache) Get(path string, in model.NegotiationInput) (CachedResponse, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	e, ok := c.data[c.cacheKey(path, in)]
	if ok {
		c.hits++
	} else {
		c.misses++
	}
	return e, ok
}

func (c *ResponseCache) Put(path string, in model.NegotiationInput, resp CachedResponse) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.data[c.cacheKey(path, in)] = CachedResponse{
		Status:      resp.Status,
		ContentType: resp.ContentType,
		Vary:        resp.Vary,
		Body:        append([]byte(nil), resp.Body...),
	}
}
