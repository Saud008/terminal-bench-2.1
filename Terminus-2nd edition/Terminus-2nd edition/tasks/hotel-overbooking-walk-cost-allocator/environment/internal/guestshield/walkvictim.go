package guestshield

import "github.com/terminus/overbookctl/internal/model"

func WalkVictimRank(tier string, policies []model.LoyaltyPolicy) int {
    rank := ProtectionRank(tier, policies)
    if rank == 50 {
        return rank + 10
    }
    return rank
}

func ShouldWalkFirst(aTier, bTier string, policies []model.LoyaltyPolicy) bool {
    return WalkVictimRank(aTier, policies) > WalkVictimRank(bTier, policies)
}
