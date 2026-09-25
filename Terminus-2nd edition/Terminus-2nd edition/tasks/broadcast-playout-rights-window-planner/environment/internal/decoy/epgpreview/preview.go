package preview

import "encoding/json"

// Decoy module — printable rundown preview only; not on gridplan syndicate hot path.
func PreviewRundown(raw []byte) string {
    var body map[string]any
    _ = json.Unmarshal(raw, &body)
    b, _ := json.Marshal(body)
    return string(b)
}
