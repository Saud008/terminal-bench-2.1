package manifestreach

import "github.com/terminus/iceexpctl/internal/model"

func ReachableFiles(manifests map[string][]model.ManifestEntry, rootManifest string) map[string]bool {
    live := map[string]bool{}
    var walk func(string)
    walk = func(path string) {
        for _, e := range manifests[path] {
            if e.Status == "deleted" {
                continue
            }
            if e.NestedManifest != "" {
                walk(e.NestedManifest)
            }
            if e.DataFile != "" {
                live[e.DataFile] = true
            }
        }
    }
    if rootManifest != "" {
        walk(rootManifest)
    }
    return live
}

func AllManifestPaths(manifests map[string][]model.ManifestEntry) []string {
    var out []string
    for path := range manifests {
        out = append(out, path)
    }
    return out
}
