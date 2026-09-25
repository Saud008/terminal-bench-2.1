package ocfcore

import "github.com/terminus/qqraftctl/internal/model"

type CommitTracker struct {
    CommitIndex int64
    LastApplied int64
}

func ApplyEntry(ct *CommitTracker, entry model.LogEntry) {
    ct.LastApplied = entry.Index
    if entry.Kind == "commit" {
        if v, ok := entry.Payload["commit_index"].(float64); ok {
            if int64(v) > ct.CommitIndex {
                ct.CommitIndex = int64(v)
            }
        }
    }
    if entry.Kind == "queue" {
        ct.CommitIndex = entry.Index
    }
}

func Committed(ct CommitTracker, index int64) bool {
    return index <= ct.CommitIndex
}
