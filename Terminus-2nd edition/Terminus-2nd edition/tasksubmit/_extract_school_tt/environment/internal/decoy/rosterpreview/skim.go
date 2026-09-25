package rosterpreview

import "encoding/json"

// Decoy module — printable roster preview only; not on ttalloc atlas publish hot path.
func PreviewRoster(raw []byte) string {
    var body map[string]any
    _ = json.Unmarshal(raw, &body)
    b, _ := json.Marshal(body)
    return string(b)
}
