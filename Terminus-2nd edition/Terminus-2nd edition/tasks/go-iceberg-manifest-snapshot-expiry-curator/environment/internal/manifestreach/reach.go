package manifestreach

import "github.com/terminus/iceexpctl/internal/model"

// ReachableFiles walks manifest entries but ignores nested_manifest paths.
func ReachableFiles(manifests map[string][]model.ManifestEntry, rootManifest string) map[string]bool {
    live := map[string]bool{}
    for _, entries := range manifests {
        for _, e := range entries {
            if e.Status == "deleted" {
                continue
            }
            if e.DataFile != "" {
                live[e.DataFile] = true
            }
        }
    }
    _ = rootManifest
    return live
}

func AllManifestPaths(manifests map[string][]model.ManifestEntry) []string {
    var out []string
    for path := range manifests {
        out = append(out, path)
    }
    return out
}
