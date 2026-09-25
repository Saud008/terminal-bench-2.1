package catalogload

import (
    "encoding/json"
    "fmt"
    "os"
    "path/filepath"
    "sort"
    "strings"

    "github.com/terminus/iceexpctl/internal/model"
)

func LoadTable(scenario, fixtureRoot string) (model.TableJSON, map[string][]model.ManifestEntry, error) {
    if fixtureRoot == "" {
        fixtureRoot = "/app/fixtures"
    }
    tablePath := filepath.Join(fixtureRoot, "tables", scenario, "table.json")
    raw, err := os.ReadFile(tablePath)
    if err != nil {
        return model.TableJSON{}, nil, err
    }
    var table model.TableJSON
    if err := json.Unmarshal(raw, &table); err != nil {
        return model.TableJSON{}, nil, err
    }
    manifestDir := filepath.Join(fixtureRoot, "tables", scenario, "manifests")
    entries, err := os.ReadDir(manifestDir)
    if err != nil {
        return model.TableJSON{}, nil, err
    }
    var metaNames []string
    for _, e := range entries {
        name := e.Name()
        if strings.HasPrefix(name, "meta_") && strings.HasSuffix(name, ".json") {
            metaNames = append(metaNames, name)
        }
    }
    sort.Strings(metaNames)
    manifests := map[string][]model.ManifestEntry{}
    for _, name := range metaNames {
        body, err := os.ReadFile(filepath.Join(manifestDir, name))
        if err != nil {
            return model.TableJSON{}, nil, err
        }
        var rows []model.ManifestEntry
        if err := json.Unmarshal(body, &rows); err != nil {
            return model.TableJSON{}, nil, err
        }
        manifests[name] = rows
    }
    return table, manifests, nil
}

func NumericMetaSort(names []string) []string {
    type item struct {
        name string
        num  int
    }
    var items []item
    for _, n := range names {
        mid := strings.TrimSuffix(strings.TrimPrefix(n, "meta_"), ".json")
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
