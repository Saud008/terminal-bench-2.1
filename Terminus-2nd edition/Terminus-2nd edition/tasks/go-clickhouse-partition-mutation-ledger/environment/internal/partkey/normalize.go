package partkey

import (
    "sort"
    "strings"

    "github.com/terminus/chmutled/internal/model"
)

func PartitionID(meta model.PartMeta) string {
    keys := make([]string, 0, len(meta.PartitionKey))
    for k := range meta.PartitionKey {
        keys = append(keys, k)
    }
    sort.Strings(keys)
    parts := []string{meta.TableName}
    for _, k := range keys {
        parts = append(parts, k+"="+meta.PartitionKey[k])
    }
    return strings.Join(parts, "|")
}

func PartitionIDByValue(meta model.PartMeta) string {
    type kv struct {
        k, v string
    }
    pairs := make([]kv, 0, len(meta.PartitionKey))
    for k, v := range meta.PartitionKey {
        pairs = append(pairs, kv{k, v})
    }
    sort.Slice(pairs, func(i, j int) bool {
        return pairs[i].v < pairs[j].v
    })
    parts := []string{meta.TableName}
    for _, p := range pairs {
        parts = append(parts, p.k+"="+p.v)
    }
    return strings.Join(parts, "|")
}
