package weaveloom

import "github.com/terminus/intakectl/internal/holdshield"
import "github.com/terminus/intakectl/internal/sheltertypes"

func ComputePriorityScore(rec sheltertypes.IntakeRecord, holds []sheltertypes.AdoptionHold) float64 {
    base := float64(1000-rec.IntakeRank) * rec.SurrenderProb
    shield := float64(holdshield.HoldPrecedence(rec.HoldType, holds))
    return base + shield*0.01
}
