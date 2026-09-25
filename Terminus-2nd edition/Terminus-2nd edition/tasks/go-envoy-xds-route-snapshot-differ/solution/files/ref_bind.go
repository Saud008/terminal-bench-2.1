package secbind

import (
    "strings"

    "github.com/terminus/xsnapctl/internal/model"
)

func CanonicalSecretID(raw string) string {
    id := strings.TrimSpace(strings.ToLower(raw))
    if !strings.HasPrefix(id, "secret/") {
        id = "secret/" + id
    }
    return id
}

func ResolveSecrets(secrets []model.SecretEntry) []model.SecretEntry {
    out := make([]model.SecretEntry, len(secrets))
    for i, sec := range secrets {
        out[i] = model.SecretEntry{
            Name:     sec.Name,
            SecretID: CanonicalSecretID(sec.SecretID),
        }
    }
    return out
}
