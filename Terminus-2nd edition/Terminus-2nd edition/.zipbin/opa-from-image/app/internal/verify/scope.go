package verify

import (
	"strings"

	"github.com/terminus/bundlectl/internal/bundle"
)

func MembersForScope(all []bundle.Member, scope string, includeMeta bool) []bundle.Member {
	out := make([]bundle.Member, 0)
	for _, m := range all {
		if includeMeta || (m.Canonical != "MANIFEST.json" && m.Canonical != ".signatures.json") {
			if strings.HasPrefix(m.Canonical, scope) || scope == "" {
				out = append(out, m)
			}
		}
	}
	return out
}

func ScopedChainRoot(all []bundle.Member, scope string, manifestOrder []string) string {
	subset := MembersForScope(all, scope, true)
	root, _ := ChainRoot(subset, manifestOrder)
	return root
}
