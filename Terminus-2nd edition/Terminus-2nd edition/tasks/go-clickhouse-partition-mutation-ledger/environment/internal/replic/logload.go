package replic

import (
    "encoding/json"
    "os"
    "path/filepath"
    "sort"

    "github.com/terminus/chmutled/internal/model"
)

func LoadDir(dir string) ([]model.ReplicaLog, error) {
    paths, err := filepath.Glob(filepath.Join(dir, "*.replica-log.jsonl"))
    if err != nil {
        return nil, err
    }
    sort.Strings(paths)
    var out []model.ReplicaLog
    for _, p := range paths {
        rows, err := loadFile(p)
        if err != nil {
            return nil, err
        }
        out = append(out, rows...)
    }
    return out, nil
}

func loadFile(path string) ([]model.ReplicaLog, error) {
    raw, err := os.ReadFile(path)
    if err != nil {
        return nil, err
    }
    var out []model.ReplicaLog
    for _, line := range splitLines(string(raw)) {
        if line == "" {
            continue
        }
        var row model.ReplicaLog
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
