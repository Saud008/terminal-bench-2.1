package breakcue

import "github.com/terminus/gridplan/internal/model"

func MarkersForProgram(_, substitutedProgram string, markers []model.AdMarker) []model.AdMarker {
    out := make([]model.AdMarker, 0)
    for _, m := range markers {
        if m.ProgramID == substitutedProgram {
            out = append(out, m)
        }
    }
    return out
}
