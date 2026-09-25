package chronorder

import "github.com/terminus/wfhistctl/internal/model"

func SortEvents(events []model.HistoryEvent) []model.HistoryEvent {
    out := append([]model.HistoryEvent(nil), events...)
    for i := 0; i < len(out); i++ {
        for j := i + 1; j < len(out); j++ {
            if out[j].Seq < out[i].Seq {
                out[i], out[j] = out[j], out[i]
            }
        }
    }
    return out
}
