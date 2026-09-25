package votercfg

import (
    "sort"

    "github.com/terminus/qqraftctl/internal/model"
)

type Set struct {
    Voters    []string
    EpochTerm int64
}

func ApplyConfig(set *Set, entry model.LogEntry) {
    if entry.Kind != "config" {
        return
    }
    if entry.Term < set.EpochTerm {
        return
    }
    set.EpochTerm = entry.Term
    op, _ := entry.Payload["op"].(string)
    node, _ := entry.Payload["node_id"].(string)
    switch op {
    case "add_voter":
        if !contains(set.Voters, node) {
            set.Voters = append(set.Voters, node)
        }
    case "remove_voter":
        set.Voters = remove(set.Voters, node)
    }
    sort.Strings(set.Voters)
}

func contains(xs []string, x string) bool {
    for _, v := range xs {
        if v == x {
            return true
        }
    }
    return false
}

func remove(xs []string, x string) []string {
    out := make([]string, 0, len(xs))
    for _, v := range xs {
        if v != x {
            out = append(out, v)
        }
    }
    return out
}
