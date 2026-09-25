package match

import (
	"strings"

	"github.com/terminus/kongadmit/internal/model"
)

func Select(routes map[string]model.Route, services map[string]model.Service, req model.MatchRequest) (model.MatchResult, bool) {
	maxLen := 0
	for _, rt := range routes {
		for _, p := range rt.Paths {
			if strings.HasPrefix(req.Path, p) && len(p) > maxLen {
				maxLen = len(p)
			}
		}
	}
	if maxLen == 0 {
		return model.MatchResult{}, false
	}

	var candidates []model.Route
	for _, rt := range routes {
		if longestPrefixLen(rt.Paths, req.Path) != maxLen {
			continue
		}
		if !methodMatches(rt.Methods, req.Method) {
			continue
		}
		candidates = append(candidates, rt)
	}
	if len(candidates) == 0 {
		return model.MatchResult{}, false
	}

	best := candidates[0]
	for _, rt := range candidates[1:] {
		if rt.Name < best.Name {
			best = rt
		}
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

func methodMatches(methods []string, reqMethod string) bool {
	if len(methods) == 0 {
		return true
	}
	for _, m := range methods {
		if strings.EqualFold(m, reqMethod) {
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
