package ledgerbuf

import (
    "bufio"
    "encoding/json"
    "os"
    "sort"

    "github.com/terminus/chmutled/internal/model"
)

func Write(path string, rows []model.StagedMutation) error {
    sort.Slice(rows, func(i, j int) bool {
        if rows[i].PartitionID != rows[j].PartitionID {
            return rows[i].PartitionID < rows[j].PartitionID
        }
        return rows[i].MutationVersion < rows[j].MutationVersion
    })
    f, err := os.Create(path)
    if err != nil {
        return err
    }
    defer f.Close()
    bw := bufio.NewWriter(f)
    for _, row := range rows {
        b, err := json.Marshal(row)
        if err != nil {
            return err
        }
        if _, err := bw.Write(b); err != nil {
            return err
        }
        if err := bw.WriteByte('\n'); err != nil {
            return err
        }
    }
    return bw.Flush()
}

func Read(path string) ([]model.StagedMutation, error) {
    raw, err := os.ReadFile(path)
    if err != nil {
        return nil, err
    }
    var out []model.StagedMutation
    for _, line := range splitLines(string(raw)) {
        if line == "" {
            continue
        }
        var row model.StagedMutation
        if err := json.Unmarshal([]byte(line), &row); err != nil {
            return nil, err
        }
        out = append(out, row)
    }
    return out, nil
}

func splitLines(s string) []string {
    var lines []string
    start := 0
    for i := 0; i < len(s); i++ {
        if s[i] == '\n' {
            lines = append(lines, s[start:i])
            start = i + 1
        }
    }
    if start < len(s) {
        lines = append(lines, s[start:])
    }
    return lines
}
