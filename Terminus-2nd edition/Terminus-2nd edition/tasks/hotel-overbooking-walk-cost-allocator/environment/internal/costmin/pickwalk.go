package costmin

import (
    "github.com/terminus/overbookctl/internal/model"
    "github.com/terminus/overbookctl/internal/tierlift"
)

type WalkChoice struct {
    ToTypeID      string
    WalkCostCents int
}

func PickWalk(fromType string, types map[string]model.RoomType, rules []model.SubstitutionRule, costs []model.WalkCost) *WalkChoice {
    choices := collectWalkChoices(fromType, types, rules, costs)
    if len(choices) == 0 {
        return nil
    }
    rankWalkChoices(choices)
    return &choices[0]
}

func collectWalkChoices(fromType string, types map[string]model.RoomType, rules []model.SubstitutionRule, costs []model.WalkCost) []WalkChoice {
    var choices []WalkChoice
    for _, wc := range costs {
        if wc.FromTypeID != fromType {
            continue
        }
        if !tierlift.AllowedUpgrade(fromType, wc.ToTypeID, types, rules) {
            continue
        }
        choices = append(choices, WalkChoice{ToTypeID: wc.ToTypeID, WalkCostCents: wc.CostCents})
    }
    return choices
}
