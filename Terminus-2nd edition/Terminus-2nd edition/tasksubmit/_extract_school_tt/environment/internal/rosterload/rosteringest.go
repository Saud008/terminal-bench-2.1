package rosterload

import "github.com/terminus/ttalloc/internal/bundleio"

// LoadBundle loads a scenario roster bundle into active state.
func LoadBundle(fixtureRoot, scenario string) error {
    return bundleio.Load(fixtureRoot, scenario)
}
