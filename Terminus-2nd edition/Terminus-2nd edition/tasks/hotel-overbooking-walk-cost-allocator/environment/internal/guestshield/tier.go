package guestshield

import "github.com/terminus/overbookctl/internal/model"

// ProtectionRank returns numeric shield; higher means more protected per loyalty-protection-contract.
func ProtectionRank(tier string, policies []model.LoyaltyPolicy) int {
    for _, p := range policies {
        if p.TierName == tier {
            return p.ProtectionRank
        }
    }
    return 999
}

// MoreProtected compares two tiers.
func MoreProtected(aTier, bTier string, policies []model.LoyaltyPolicy) bool {
    return ProtectionRank(aTier, policies) > ProtectionRank(bTier, policies)
}
