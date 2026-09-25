package router

import (
	"sort"

	"github.com/terminus/temporal-signal-replay/internal/model"
)

// ResolveVersion picks the workflow handler version for signal delivery.
func ResolveVersion(sc model.Scenario) string {
	if len(sc.VersionsRegistered) == 0 {
		return sc.PinnedVersion
	}
	versions := append([]string(nil), sc.VersionsRegistered...)
	sort.Strings(versions)
	return versions[len(versions)-1]
}
