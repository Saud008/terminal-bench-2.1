package logparse

import (
    "bufio"
    "encoding/json"
    "os"
    "path/filepath"
    "sort"

    "github.com/terminus/qqraftctl/internal/model"
)

func ReadClusterLogs(dir string) ([]model.LogEntry, error) {
    paths, err := filepath.Glob(filepath.Join(dir, "*.qlog"))
    if err != nil {
        return nil, err
    }
    sort.Strings(paths)
    var out []model.LogEntry
    for _, p := range paths {
        rows, err := readFile(p)
        if err != nil {
            return nil, err
        }
        out = append(out, rows...)
    }
    sort.Slice(out, func(i, j int) bool {
        return out[i].Index < out[j].Index
    })
    return out, nil
}

func readFile(path string) ([]model.LogEntry, error) {
    f, err := os.Open(path)
    if err != nil {
        return nil, err
    }
    defer f.Close()
    var rows []model.LogEntry
    sc := bufio.NewScanner(f)
    for sc.Scan() {
        var row model.LogEntry
        if err := json.Unmarshal(sc.Bytes(), &row); err != nil {
            return nil, err
        }
        rows = append(rows, row)
    }
    return rows, sc.Err()
}
