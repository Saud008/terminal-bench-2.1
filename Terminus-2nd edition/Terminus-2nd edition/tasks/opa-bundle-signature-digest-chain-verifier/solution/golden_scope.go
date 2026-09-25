package verify

import (
	"strings"

	"github.com/terminus/bundlectl/internal/bundle"
)

func MembersForScope(all []bundle.Member, scope string, includeMeta bool) []bundle.Member {
	out := make([]bundle.Member, 0)
	for _, m := range all {
		if !includeMeta && (m.Canonical == "MANIFEST.json" || m.Canonical == ".signatures.json") {
			continue
		}
		if scope == "" || strings.HasPrefix(m.Canonical, scope) {
			out = append(out, m)
		}
	}
	return out
}

func ScopedChainRoot(all []bundle.Member, scope string, _ []string) string {
	subset := MembersForScope(all, scope, false)
	root, _ := SortedChainRoot(subset)
	return root
}
