package speciesgate

import "github.com/terminus/intakectl/internal/sheltertypes"

func AllowedUpgrade(fromSpecies, toSpecies string, profiles map[string]sheltertypes.SpeciesProfile, rules []sheltertypes.KennelCompatRule) bool {
    for _, r := range rules {
        if r.FromSpecies != fromSpecies || r.ToSpecies != toSpecies {
            continue
        }
        from, okFrom := profiles[fromSpecies]
        to, okTo := profiles[toSpecies]
        if !okFrom || !okTo {
            return false
        }
        return to.IsolationRank > from.IsolationRank
    }
    return false
}
