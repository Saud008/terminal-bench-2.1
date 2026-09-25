package xferpick

import (
    "sort"

    "github.com/terminus/intakectl/internal/speciesgate"
    "github.com/terminus/intakectl/internal/sheltertypes"
)

type TransferChoice struct {
    ToSpecies       string
    TransferPenalty int
}

func PickTransfer(fromSpecies string, profiles map[string]sheltertypes.SpeciesProfile, rules []sheltertypes.KennelCompatRule, penalties []sheltertypes.TransferPenalty) *TransferChoice {
    var choices []TransferChoice
    for _, tp := range penalties {
        if tp.FromSpecies != fromSpecies {
            continue
        }
        if !speciesgate.AllowedUpgrade(fromSpecies, tp.ToSpecies, profiles, rules) {
            continue
        }
        choices = append(choices, TransferChoice{ToSpecies: tp.ToSpecies, TransferPenalty: tp.TransferPenalty})
    }
    if len(choices) == 0 {
        return nil
    }
    sort.Slice(choices, func(i, j int) bool {
        if choices[i].TransferPenalty != choices[j].TransferPenalty {
            return choices[i].TransferPenalty > choices[j].TransferPenalty
        }
        return choices[i].ToSpecies > choices[j].ToSpecies
    })
    return &choices[0]
}
