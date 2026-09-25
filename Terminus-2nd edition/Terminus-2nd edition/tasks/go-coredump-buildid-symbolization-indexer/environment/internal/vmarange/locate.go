package vmarange

import (
    "sort"
    "strconv"
    "strings"

    "github.com/terminus/coreidx/internal/model"
)

type Hit struct {
    Entry      model.MmapEntry
    FileOffset uint64
}

func LocatePC(pcHex string, mmaps []model.MmapEntry) (Hit, bool) {
    pc, err := parseHex(pcHex)
    if err != nil {
        return Hit{}, false
    }
    var hits []Hit
    for _, m := range mmaps {
        start, err1 := parseHex(m.Start)
        end, err2 := parseHex(m.End)
        off, err3 := parseHex(m.FileOffset)
        if err1 != nil || err2 != nil || err3 != nil {
            continue
        }
        if start <= pc && pc <= end {
            hits = append(hits, Hit{Entry: m, FileOffset: off})
        }
    }
    if len(hits) == 0 {
        return Hit{}, false
    }
    sort.Slice(hits, func(i, j int) bool {
        return hits[i].FileOffset > hits[j].FileOffset
    })
    return hits[0], true
}

func FileRelativeOffset(pcHex string, hit Hit) (uint64, bool) {
    pc, err := parseHex(pcHex)
    if err != nil {
        return 0, false
    }
    if pc < hit.FileOffset {
        return 0, false
    }
    return pc - hit.FileOffset, true
}

func parseHex(s string) (uint64, error) {
    s = strings.TrimPrefix(strings.ToLower(s), "0x")
    return strconv.ParseUint(s, 16, 64)
}
