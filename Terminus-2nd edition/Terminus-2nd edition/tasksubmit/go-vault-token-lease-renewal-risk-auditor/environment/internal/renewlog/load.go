package renewlog

import (
    "bufio"
    "encoding/json"
    "os"
    "path/filepath"
    "sort"
    "strings"

    "github.com/terminus/vaultaud/internal/model"
)

func LoadDir(dir string) ([]model.RenewalEvent, error) {
    entries, err := os.ReadDir(dir)
    if err != nil {
        return nil, err
    }
    var paths []string
    for _, e := range entries {
        if e.IsDir() {
            continue
        }
        if strings.HasSuffix(e.Name(), ".lease-renew.jsonl") {
            paths = append(paths, filepath.Join(dir, e.Name()))
        }
    }
    sort.Strings(paths)
    var out []model.RenewalEvent
    for _, p := range paths {
        rows, err := loadFile(p)
        if err != nil {
            return nil, err
        }
        out = append(out, rows...)
    }
    return out, nil
}

func loadFile(path string) ([]model.RenewalEvent, error) {
    f, err := os.Open(path)
    if err != nil {
        return nil, err
    }
    defer f.Close()
    var out []model.RenewalEvent
    sc := bufio.NewScanner(f)
    for sc.Scan() {
        line := strings.TrimSpace(sc.Text())
        if line == "" {
            continue
        }
        var ev model.RenewalEvent
        if err := json.Unmarshal([]byte(line), &ev); err != nil {
            return nil, err
        }
        out = append(out, ev)
    }
    return out, sc.Err()
}
