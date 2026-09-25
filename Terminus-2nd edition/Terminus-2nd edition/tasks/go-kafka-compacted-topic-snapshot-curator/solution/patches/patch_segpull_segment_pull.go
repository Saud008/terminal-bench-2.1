package segpull

import (
    "bufio"
    "encoding/json"
    "fmt"
    "os"
    "path/filepath"
    "sort"
    "strings"

    "github.com/terminus/kcompactctl/internal/keyfold"
    "github.com/terminus/kcompactctl/internal/model"
)

func LoadTopic(topic, scenario, fixtureRoot string) ([]model.StagedRecord, int, error) {
    root := fixtureRoot
    if root == "" {
        root = "/app/fixtures"
    }
    segDir := filepath.Join(root, "compact-logs", scenario, "segments")
    entries, err := os.ReadDir(segDir)
    if err != nil {
        return nil, 0, err
    }
    var segNames []string
    for _, e := range entries {
        if !e.IsDir() && strings.HasPrefix(e.Name(), "seg_") && strings.HasSuffix(e.Name(), ".jsonl") {
            segNames = append(segNames, e.Name())
        }
    }
    segNames = NumericSegSort(segNames)

    var staged []model.StagedRecord
    for _, name := range segNames {
        f, err := os.Open(filepath.Join(segDir, name))
        if err != nil {
            return nil, 0, err
        }
        sc := bufio.NewScanner(f)
        for sc.Scan() {
            line := strings.TrimSpace(sc.Text())
            if line == "" {
                continue
            }
            var rec model.SegmentRecord
            if err := json.Unmarshal([]byte(line), &rec); err != nil {
                f.Close()
                return nil, 0, err
            }
            staged = append(staged, model.StagedRecord{
                Partition:    rec.Partition,
                Offset:       rec.Offset,
                TimestampMs:  rec.TimestampMs,
                KeyRaw:       rec.KeyRaw,
                CanonicalKey: keyfold.Canonical(rec.KeyRaw),
                ValueRaw:     rec.ValueRaw,
                IsTombstone:  rec.IsTombstone,
            })
        }
        f.Close()
        if err := sc.Err(); err != nil {
            return nil, 0, err
        }
    }
    return staged, len(segNames), nil
}

func NumericSegSort(names []string) []string {
    type item struct {
        name string
        num  int
    }
    var items []item
    for _, n := range names {
        mid := strings.TrimSuffix(strings.TrimPrefix(n, "seg_"), ".jsonl")
        var num int
        fmt.Sscanf(mid, "%d", &num)
        items = append(items, item{name: n, num: num})
    }
    sort.Slice(items, func(i, j int) bool { return items[i].num < items[j].num })
    out := make([]string, len(items))
    for i, it := range items {
        out[i] = it.name
    }
    return out
}
