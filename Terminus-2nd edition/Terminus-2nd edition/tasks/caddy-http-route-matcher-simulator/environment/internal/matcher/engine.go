package matcher

import (
	"github.com/terminus/caddyctl/internal/types"
)

// SelectWinner picks the winning route for a request (broken: first array match).
func SelectWinner(st *types.StageFile, req *HTTPRequest) (types.RouteRow, bool) {
	for _, route := range st.Routes {
		if routeMatches(route, req) {
			return route, true
		}
	}
	return types.RouteRow{}, false
}

func routeMatches(route types.RouteRow, req *HTTPRequest) bool {
	if len(route.Matchers) == 0 {
		return false
	}
	for _, block := range route.Matchers {
		if !blockMatches(block, req) {
			return false
		}
	}
	return true
}

func blockMatches(block types.MatcherBlock, req *HTTPRequest) bool {
	if len(block.Method) > 0 && !methodMatches(block.Method, req.Method) {
		return false
	}
	if len(block.Path) > 0 && !pathPrefixMatches(block.Path, req.Path) {
		return false
	}
	if len(block.PathRegexp) > 0 && !pathRegexpMatches(block.PathRegexp, req.Path) {
		return false
	}
	if len(block.Header) > 0 && !headerMatches(block.Header, req.Headers, false) {
		return false
	}
	return true
}

func methodMatches(allowed []string, method string) bool {
	for _, m := range allowed {
		if m == method {
			return true
		}
	}
	return false
}

func pathPrefixMatches(patterns []string, path string) bool {
	for _, p := range patterns {
		if matchPathPattern(p, path) {
			return true
		}
	}
	return false
}

func matchPathPattern(pattern, path string) bool {
	if stringsHasSuffixStar(pattern) {
		prefix := pattern[:len(pattern)-1]
		return len(path) >= len(prefix) && path[:len(prefix)] == prefix
	}
	return pattern == path
}

func stringsHasSuffixStar(s string) bool {
	return len(s) > 0 && s[len(s)-1] == '*'
}
