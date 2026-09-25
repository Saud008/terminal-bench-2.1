package fault

import (
	"hash/fnv"
	"sort"
)

type Case struct {
	ID   string
	Mode string
}

var BaseCases = []Case{
	{ID: "trailer-split", Mode: "unary"},
	{ID: "status-details", Mode: "unary"},
	{ID: "ctx-cancel", Mode: "unary"},
	{ID: "recv-limit-body", Mode: "unary"},
	{ID: "unary-shape", Mode: "unary"},
	{ID: "stream-shape", Mode: "stream"},
}

type Catalog struct {
	Seed       string
	TrailerKey string
	DetailKey  string
	Cases      []Case
}

func Configure(seed string) Catalog {
	h := fnv.New64a()
	_, _ = h.Write([]byte(seed))
	n := h.Sum64()
	return Catalog{
		Seed:       seed,
		TrailerKey: trailerKeys[int(n)%len(trailerKeys)],
		DetailKey:  detailKeys[int(n>>8)%len(detailKeys)],
		Cases:      append([]Case(nil), BaseCases...),
	}
}

var (
	trailerKeys = []string{"x-trace-tail", "x-audit-tail", "x-tenant-tail"}
	detailKeys  = []string{"fault-domain", "fault-reason", "fault-scope"}
)

func CaseIDs(c Catalog) []string {
	out := make([]string, len(c.Cases))
	for i, item := range c.Cases {
		out[i] = item.ID
	}
	sort.Strings(out)
	return out
}
