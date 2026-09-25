package jwksort

import (
    "sort"

    "github.com/terminus/spiffectl/internal/model"
)

func OrderKeys(keys []model.JWKSKey) []model.JWKSKey {
    var sig, enc []model.JWKSKey
    for _, k := range keys {
        if k.Use == "sig" {
            sig = append(sig, k)
        } else {
            enc = append(enc, k)
        }
    }
    sort.Slice(sig, func(i, j int) bool { return sig[i].KID < sig[j].KID })
    sort.Slice(enc, func(i, j int) bool { return enc[i].KID < enc[j].KID })
    return append(sig, enc...)
}
