package lineswap

import "github.com/terminus/gridplan/internal/model"

func ResolveProgram(program model.Program, feeds []model.Feed) string {
    for _, f := range feeds {
        if f.FeedID != program.FeedID {
            continue
        }
        if sub, ok := f.Substitutions[program.ProgramID]; ok {
            return sub
        }
    }
    return program.ProgramID
}
