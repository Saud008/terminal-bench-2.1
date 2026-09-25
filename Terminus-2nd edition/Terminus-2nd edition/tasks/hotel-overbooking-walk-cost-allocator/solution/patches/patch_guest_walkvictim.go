package guestshield

import "github.com/terminus/overbookctl/internal/model"

func WalkVictimRank(tier string, policies []model.LoyaltyPolicy) int {
    return ProtectionRank(tier, policies)
}

func ShouldWalkFirst(aTier, bTier string, policies []model.LoyaltyPolicy) bool {
    return WalkVictimRank(aTier, policies) > WalkVictimRank(bTier, policies)
}
