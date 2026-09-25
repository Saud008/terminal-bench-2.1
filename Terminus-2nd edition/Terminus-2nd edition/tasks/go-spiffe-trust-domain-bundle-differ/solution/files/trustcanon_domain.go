package trustcanon

import "strings"

func FoldTrustDomainHost(raw string) string {
    td := strings.TrimSpace(raw)
    if strings.HasPrefix(strings.ToLower(td), "spiffe://") {
        td = td[len("spiffe://"):]
    }
    return strings.ToLower(td)
}

func FoldSPIFFEURI(raw string) string {
    id := strings.TrimSpace(raw)
    if !strings.HasPrefix(strings.ToLower(id), "spiffe://") {
        id = "spiffe://" + id
    }
    slash := strings.Index(id[9:], "/")
    if slash == -1 {
        return strings.ToLower(id)
    }
    host := strings.ToLower(id[9 : 9+slash])
    return "spiffe://" + host + strings.ToLower(id[9+slash:])
}
