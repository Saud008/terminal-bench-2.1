package vaccinecheck

import (
    "time"

    "github.com/terminus/intakectl/internal/sheltertypes"
)

func minValidDays(speciesCode string, policies []sheltertypes.VaccinationPolicy) int {
    for _, p := range policies {
        if p.SpeciesCode == speciesCode {
            return p.MinValidDays
        }
    }
    return 0
}

func daysRemaining(validUntil, intakeDate string) int {
    layout := "2006-01-02"
    end, err := time.Parse(layout, validUntil)
    if err != nil {
        return -1
    }
    start, err := time.Parse(layout, intakeDate)
    if err != nil {
        return -1
    }
    return int(end.Sub(start).Hours() / 24)
}

func VaccineEligible(rec sheltertypes.IntakeRecord, intakeDate string, policies []sheltertypes.VaccinationPolicy) bool {
    minDays := minValidDays(rec.SpeciesCode, policies)
    remaining := daysRemaining(rec.VaccValidUntil, intakeDate)
    return remaining > minDays
}
