package match

import (
	"strings"

	"github.com/terminus/kongadmit/internal/model"
)

func Select(routes map[string]model.Route, services map[string]model.Service, req model.MatchRequest) (model.MatchResult, bool) {
	var best model.Route
	bestLen := -1
	found := false
	for _, rt := range routes {
		if !pathMatches(rt.Paths, req.Path) {
			continue
		}
		plen := longestPrefixLen(rt.Paths, req.Path)
		if plen > bestLen {
			bestLen = plen
			best = rt
			found = true
		}
	}
	if !found {
		return model.MatchResult{}, false
	}
	svc, ok := services[best.Service]
	if !ok {
		return model.MatchResult{}, false
	}
	return model.MatchResult{Route: best, Service: svc}, true
}

func pathMatches(paths []string, reqPath string) bool {
	for _, p := range paths {
		if strings.HasPrefix(reqPath, p) {
			return true
		}
	}
	return false
}

func longestPrefixLen(paths []string, reqPath string) int {
	best := 0
	for _, p := range paths {
		if strings.HasPrefix(reqPath, p) && len(p) > best {
			best = len(p)
		}
	}
	return best
}
