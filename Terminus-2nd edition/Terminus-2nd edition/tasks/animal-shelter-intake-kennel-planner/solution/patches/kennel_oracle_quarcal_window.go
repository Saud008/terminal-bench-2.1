package quarcal

import "github.com/terminus/intakectl/internal/sheltertypes"

func KennelQuarantined(kennelID, intakeDate string, windows []sheltertypes.QuarantineWindow) bool {
    for _, w := range windows {
        if w.KennelID != kennelID {
            continue
        }
        if intakeDate >= w.StartDate && intakeDate <= w.EndDate {
            return true
        }
    }
    return false
}
