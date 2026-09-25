package blackoutcal

import "github.com/terminus/overbookctl/internal/model"

func windowCoversDate(w model.Maintenance, nightDate string) bool {
    if nightDate < w.StartDate {
        return false
    }
    return nightDate <= w.EndDate
}
