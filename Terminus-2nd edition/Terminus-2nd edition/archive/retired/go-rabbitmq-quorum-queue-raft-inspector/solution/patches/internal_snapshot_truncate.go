package bundleclip

import "github.com/terminus/qqraftctl/internal/model"

func FilterAfterSnapshot(entries []model.LogEntry, snap model.Snapshot) []model.LogEntry {
    cutoff := snap.LastIncludedIndex
    var out []model.LogEntry
    for _, e := range entries {
        if e.Index > cutoff {
            out = append(out, e)
        }
    }
    return out
}

func LoadBaseline(snap model.Snapshot) (map[string]int64, []string, int64) {
    qs := map[string]int64{}
    for k, v := range snap.QueueStates {
        qs[k] = v
    }
    mem := append([]string(nil), snap.Membership...)
    return qs, mem, snap.CommitIndex
}
