package chronorder

import "github.com/terminus/wfhistctl/internal/model"

func SortEvents(events []model.HistoryEvent) []model.HistoryEvent {
    out := append([]model.HistoryEvent(nil), events...)
    for i := 0; i < len(out); i++ {
        for j := i + 1; j < len(out); j++ {
            ai, aj := out[i], out[j]
            less := ai.TimestampMs > aj.TimestampMs ||
                (ai.TimestampMs == aj.TimestampMs && (ai.EventID > aj.EventID ||
                    (ai.EventID == aj.EventID && ai.Seq > aj.Seq)))
            if less {
                out[i], out[j] = out[j], out[i]
            }
        }
    }
    return out
}
