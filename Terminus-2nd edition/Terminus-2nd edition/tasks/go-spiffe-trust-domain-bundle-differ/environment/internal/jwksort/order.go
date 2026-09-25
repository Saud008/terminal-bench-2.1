package jwksort

import (
    "sort"

    "github.com/terminus/spiffectl/internal/model"
)

func OrderKeys(keys []model.JWKSKey) []model.JWKSKey {
    out := make([]model.JWKSKey, len(keys))
    copy(out, keys)
    sort.Slice(out, func(i, j int) bool {
        return out[i].KID < out[j].KID
    })
    return out
}
