package bundleio

import (
    "bufio"
    "encoding/json"
    "os"
    "path/filepath"
    "sort"
    "strings"

    "github.com/terminus/coreidx/internal/model"
)

func LoadCrashDir(dir string) ([]model.CrashRecord, error) {
    entries, err := os.ReadDir(dir)
    if err != nil {
        return nil, err
    }
    var paths []string
    for _, e := range entries {
        if e.IsDir() {
            continue
        }
        if strings.HasSuffix(e.Name(), ".crash.jsonl") {
            paths = append(paths, filepath.Join(dir, e.Name()))
        }
    }
    sort.Strings(paths)
    var out []model.CrashRecord
    for _, p := range paths {
        rows, err := loadFile(p)
        if err != nil {
            return nil, err
        }
        out = append(out, rows...)
    }
    return out, nil
}

func loadFile(path string) ([]model.CrashRecord, error) {
    f, err := os.Open(path)
    if err != nil {
        return nil, err
    }
    defer f.Close()
    var out []model.CrashRecord
    sc := bufio.NewScanner(f)
    for sc.Scan() {
        line := strings.TrimSpace(sc.Text())
        if line == "" {
            continue
        }
        var rec model.CrashRecord
        if err := json.Unmarshal([]byte(line), &rec); err != nil {
            return nil, err
        }
        out = append(out, rec)
    }
    return out, sc.Err()
}
