package holdshield

import "github.com/terminus/intakectl/internal/sheltertypes"

func HoldPrecedence(holdType string, holds []sheltertypes.AdoptionHold) int {
    for _, h := range holds {
        if h.HoldType == holdType {
            return h.PrecedenceRank
        }
    }
    return 999
}

func StrongerHold(aHold, bHold string, holds []sheltertypes.AdoptionHold) bool {
    return HoldPrecedence(aHold, holds) > HoldPrecedence(bHold, holds)
}
