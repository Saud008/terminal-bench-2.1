package keysout

import (
    "encoding/json"
    "fmt"
    "os"
    "path/filepath"
    "sort"

    "github.com/terminus/kcompactctl/internal/model"
    "github.com/terminus/kcompactctl/internal/offsetdup"
    "github.com/terminus/kcompactctl/internal/partitionorder"
    "github.com/terminus/kcompactctl/internal/latestmap"
    "github.com/terminus/kcompactctl/internal/coldstore"
    "github.com/terminus/kcompactctl/internal/tombwin"
)

const (
    defaultSnap = "/app/output/topic-key-snapshot.jsonl"
    defaultLin  = "/app/output/tombstone-lineage.jsonl"
    genPath     = "/app/state/compact-curator-seal.json"
)

func Emit(topic, scenario, snapPath, linPath string) error {
    var gen model.CuratorSealFile
    raw, err := os.ReadFile(genPath)
    if err != nil {
        return fmt.Errorf("curator_seal missing")
    }
    if err := json.Unmarshal(raw, &gen); err != nil {
        return err
    }
    if gen.CuratorSeal <= 0 {
        return fmt.Errorf("publish blocked: curator_seal must be > 0")
    }
    snap, err := coldstore.ReadStage("")
    if err != nil {
        return err
    }
    ordered := partitionorder.OrderRecords(snap.Records)
    collapsed := offsetdup.Collapse(ordered)
    result := latestmap.ComposeTable(collapsed, tombwin.RetentionMs())
    if snapPath == "" {
        snapPath = defaultSnap
    }
    if linPath == "" {
        linPath = defaultLin
    }
    if err := writeSnapshot(snapPath, result.Rows); err != nil {
        return err
    }
    return writeLineage(linPath, result.Lineage)
}

// Snapshot rows sorted by partition then offset for export.
func writeSnapshot(path string, rows []model.SnapshotRow) error {
    if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
        return err
    }
    sort.Slice(rows, func(i, j int) bool {
        if rows[i].Partition != rows[j].Partition {
            return rows[i].Partition < rows[j].Partition
        }
        return rows[i].Offset < rows[j].Offset
    })
    var buf []byte
    for _, row := range rows {
        line, err := json.Marshal(row)
        if err != nil {
            return err
        }
        buf = append(buf, line...)
        buf = append(buf, '\n')
    }
    return os.WriteFile(path, buf, 0o644)
}

func writeLineage(path string, rows []model.LineageRow) error {
    if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
        return err
    }
    sort.Slice(rows, func(i, j int) bool {
        if rows[i].Partition != rows[j].Partition {
            return rows[i].Partition < rows[j].Partition
        }
        return rows[i].Offset < rows[j].Offset
    })
    var buf []byte
    for _, row := range rows {
        line, err := json.Marshal(row)
        if err != nil {
            return err
        }
        buf = append(buf, line...)
        buf = append(buf, '\n')
    }
    return os.WriteFile(path, buf, 0o644)
}
