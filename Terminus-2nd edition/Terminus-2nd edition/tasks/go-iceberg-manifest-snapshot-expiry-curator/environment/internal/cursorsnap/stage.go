package cursorsnap

import (
    "bytes"
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "os"
    "path/filepath"

    "github.com/terminus/iceexpctl/internal/catalogload"
    "github.com/terminus/iceexpctl/internal/model"
)

const DefaultStagePath = "/app/state/table-cursor.json"

func WriteStage(path string, snap model.CursorSnapshot) error {
    if path == "" {
        path = DefaultStagePath
    }
    if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
        return err
    }
    digest, err := computeDigest(snap.Table, snap.Manifests)
    if err != nil {
        return err
    }
    snap.CursorSeal = digest
    data, err := json.MarshalIndent(snap, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile(path, data, 0o644)
}

func ReadStage(path string) (model.CursorSnapshot, error) {
    if path == "" {
        path = DefaultStagePath
    }
    raw, err := os.ReadFile(path)
    if err != nil {
        return model.CursorSnapshot{}, err
    }
    var snap model.CursorSnapshot
    if err := json.Unmarshal(raw, &snap); err != nil {
        return model.CursorSnapshot{}, err
    }
    return snap, nil
}

func computeDigest(table model.TableJSON, manifests map[string][]model.ManifestEntry) (string, error) {
    tableCopy := table

    keys := make([]string, 0, len(manifests))
    for k := range manifests {
        keys = append(keys, k)
    }
    keys = catalogload.NumericMetaSort(keys)

    var buf bytes.Buffer
    buf.WriteString(`{"manifests":{`)
    for i, name := range keys {
        if i > 0 {
            buf.WriteByte(',')
        }
        keyJSON, err := json.Marshal(name)
        if err != nil {
            return "", err
        }
        buf.Write(keyJSON)
        buf.WriteByte(':')
        valJSON, err := json.Marshal(manifests[name])
        if err != nil {
            return "", err
        }
        buf.Write(valJSON)
    }
    buf.WriteString(`,"table":`)
    tableJSON, err := json.Marshal(tableCopy)
    if err != nil {
        return "", err
    }
    buf.Write(tableJSON)
    buf.WriteByte('}')

    sum := sha256.Sum256(buf.Bytes())
    return hex.EncodeToString(sum[:]), nil
}
