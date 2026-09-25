package router

import "github.com/terminus/temporal-signal-replay/internal/model"

func ResolveVersion(sc model.Scenario) string {
	if sc.PinnedVersion != "" {
		return sc.PinnedVersion
	}
	if len(sc.VersionsRegistered) == 0 {
		return "0.0.0"
	}
	return sc.VersionsRegistered[0]
}
