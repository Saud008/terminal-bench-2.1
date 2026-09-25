package match

import (
	"regexp"
	"strings"

	"github.com/terminus/caddyroute/internal/types"
)

// RouteMatches evaluates matchers against a parsed HTTP request.
func RouteMatches(matchers []types.Matcher, req types.HTTPRequest, terminal bool) bool {
	if len(matchers) == 0 {
		return false
	}
	for _, m := range matchers {
		if !methodOK(m.Method, req.Method) {
			return false
		}
		if !pathOK(m.Path, req.Path) {
			return false
		}
		if !pathRegexpOK(m.PathRegexp, req.Path) {
			return false
		}
		if !headerOK(m, req.Headers) {
			return false
		}
	}
	_ = terminal
	return true
}

func methodOK(allowed []string, method string) bool {
	if len(allowed) == 0 {
		return true
	}
	for _, m := range allowed {
		if strings.EqualFold(m, method) {
			return true
		}
	}
	return false
}

func pathOK(patterns []string, path string) bool {
	if len(patterns) == 0 {
		return true
	}
	for _, p := range patterns {
		if strings.HasSuffix(p, "*") {
			prefix := strings.TrimSuffix(p, "*")
			if strings.HasPrefix(path, prefix) {
				return true
			}
		} else if path == p {
			return true
		}
	}
	return false
}

func pathRegexpOK(patterns []string, path string) bool {
	if len(patterns) == 0 {
		return true
	}
	for _, pat := range patterns {
		re, err := regexp.Compile(pat)
		if err != nil {
			continue
		}
		if re.FindStringIndex(path) != nil {
			return true
		}
	}
	return false
}

func headerOK(m types.Matcher, headers map[string]string) bool {
	if len(m.Header) == 0 {
		return true
	}
	for name, wantVals := range m.Header {
		var got string
		for hk, hv := range headers {
			if strings.EqualFold(hk, name) {
				got = hv
				break
			}
		}
		if got == "" {
			return false
		}
		sensitive := false
		if m.CaseSensitive != nil {
			sensitive = *m.CaseSensitive
		}
		matched := false
		for _, want := range wantVals {
			if sensitive {
				if got == want {
					matched = true
					break
				}
			} else if strings.EqualFold(got, want) {
				if got == want {
					matched = true
					break
				}
			}
		}
		if !matched {
			return false
		}
	}
	return true
}
