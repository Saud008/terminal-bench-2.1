package tierlift

import "github.com/terminus/overbookctl/internal/model"

// AllowedUpgrade reports whether substitution from->to is permitted.
func AllowedUpgrade(fromType, toType string, types map[string]model.RoomType, rules []model.SubstitutionRule) bool {
    for _, r := range rules {
        if r.FromTypeID != fromType || r.ToTypeID != toType {
            continue
        }
        from, okFrom := types[fromType]
        to, okTo := types[toType]
        if !okFrom || !okTo {
            return false
        }
        return to.Rank > from.Rank
    }
    return false
}
