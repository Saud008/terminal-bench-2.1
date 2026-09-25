package breakcue

import "github.com/terminus/gridplan/internal/model"

func MarkersForProgram(originalProgram, substitutedProgram string, markers []model.AdMarker) []model.AdMarker {
    if originalProgram != substitutedProgram {
        return nil
    }
    out := make([]model.AdMarker, 0)
    for _, m := range markers {
        if m.ProgramID == originalProgram {
            out = append(out, m)
        }
    }
    return out
}
