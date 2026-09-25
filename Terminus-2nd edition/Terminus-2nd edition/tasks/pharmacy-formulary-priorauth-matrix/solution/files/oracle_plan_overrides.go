package planrule

import "github.com/terminus/formulatrix/internal/model"

func SelectOverride(rules []model.Override, planID, ndc, asOf string) (model.Override, bool) {
    var tier []model.Override
    for _, r := range rules {
        if r.PlanID != planID || r.NDC != ndc {
            continue
        }
        if !DateActive(r.EffectiveStart, r.EffectiveEnd, asOf) {
            continue
        }
        tier = append(tier, r)
    }
    if len(tier) == 0 {
        return model.Override{}, false
    }
    bestPriority := tier[0].Priority
    for _, r := range tier {
        if r.Priority > bestPriority {
            bestPriority = r.Priority
        }
    }
    var best model.Override
    found := false
    for _, r := range tier {
        if r.Priority != bestPriority {
            continue
        }
        if !found || TieBreakStart(r.EffectiveStart, best.EffectiveStart) == r.EffectiveStart {
            best = r
            found = true
        }
    }
    return best, found
}
