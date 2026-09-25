package revsnap

import "github.com/terminus/overbookctl/internal/guestshield"
import "github.com/terminus/overbookctl/internal/model"

func ComputeDemandScore(res model.Reservation, policies []model.LoyaltyPolicy) float64 {
    base := float64(1000-res.ArrivalRank) * res.CancelProb
    shield := float64(guestshield.ProtectionRank(res.LoyaltyTier, policies))
    return base + shield*0.01
}
