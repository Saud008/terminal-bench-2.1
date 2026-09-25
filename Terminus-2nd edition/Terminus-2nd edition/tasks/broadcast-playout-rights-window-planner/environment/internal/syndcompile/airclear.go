package syndcompile

import (
    "github.com/terminus/gridplan/internal/darkregion"
    "github.com/terminus/gridplan/internal/model"
    "github.com/terminus/gridplan/internal/windowpick"
)

func airRightsStatus(resolved, region, startUTC, airDate string, rights []model.RightsContract, blackouts []model.Blackout) string {
    _, rightsOK := windowpick.PickContract(resolved, region, airDate, rights)
    status := "cleared"
    if !rightsOK {
        status = "rights_denied"
    }
    if darkregion.Blocked(region, startUTC, blackouts, rightsOK) {
        status = "blackout"
    }
    return status
}
