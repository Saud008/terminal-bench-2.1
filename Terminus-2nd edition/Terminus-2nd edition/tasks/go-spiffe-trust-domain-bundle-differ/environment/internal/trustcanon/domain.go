package trustcanon

import "strings"

func FoldTrustDomainHost(raw string) string {
    td := strings.TrimSpace(raw)
    if strings.HasPrefix(td, "spiffe://") {
        td = strings.TrimPrefix(td, "spiffe://")
    }
    return td
}

func FoldSPIFFEURI(raw string) string {
    id := strings.TrimSpace(raw)
    if !strings.HasPrefix(id, "spiffe://") {
        id = "spiffe://" + id
    }
    return id
}
