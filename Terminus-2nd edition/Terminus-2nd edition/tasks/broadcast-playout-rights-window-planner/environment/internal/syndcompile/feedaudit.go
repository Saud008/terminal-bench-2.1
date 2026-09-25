package syndcompile

import (
    "github.com/terminus/gridplan/internal/breakcue"
    "github.com/terminus/gridplan/internal/lineswap"
    "github.com/terminus/gridplan/internal/model"
)

func feedMarkerAudit(prog model.Program, bundle *model.ScheduleBundle) (string, int) {
    resolved := lineswap.ResolveProgram(prog, bundle.Feeds)
    markers := breakcue.MarkersForProgram(prog.ProgramID, resolved, bundle.AdMarkers)
    return resolved, len(markers)
}
