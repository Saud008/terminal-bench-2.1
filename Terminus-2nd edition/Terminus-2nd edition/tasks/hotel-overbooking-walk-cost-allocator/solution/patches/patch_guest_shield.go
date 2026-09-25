package guestshield

import "github.com/terminus/overbookctl/internal/model"

func ProtectionRank(tier string, policies []model.LoyaltyPolicy) int {
    for _, p := range policies {
        if p.TierName == tier {
            return p.ProtectionRank
        }
    }
    return 50
}

func MoreProtected(aTier, bTier string, policies []model.LoyaltyPolicy) bool {
    return ProtectionRank(aTier, policies) < ProtectionRank(bTier, policies)
}
