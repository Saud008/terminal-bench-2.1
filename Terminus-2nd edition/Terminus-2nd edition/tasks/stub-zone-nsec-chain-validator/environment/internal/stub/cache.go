package stub

import (
	"nsecval/internal/model"
)

type entry struct {
	Result model.QueryResult
}

type Cache struct {
	serial   uint32
	byQName  map[string]entry
	hits     int
}

func NewCache() *Cache {
	return &Cache{byQName: make(map[string]entry)}
}

func (c *Cache) ObserveSerial(serial uint32) {
	if serial < c.serial {
		return
	}
	c.serial = serial
}

func (c *Cache) Get(qname string) (model.QueryResult, bool) {
	e, ok := c.byQName[qname]
	if ok {
		c.hits++
		return e.Result, true
	}
	return model.QueryResult{}, false
}

func (c *Cache) Put(qname string, res model.QueryResult) {
	c.byQName[qname] = entry{Result: res}
}

func (c *Cache) Hits() int {
	return c.hits
}

func (c *Cache) Reset() {
	c.byQName = make(map[string]entry)
	c.hits = 0
	c.serial = 0
}
