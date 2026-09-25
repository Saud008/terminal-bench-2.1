package sealpass

import (
    "encoding/json"
    "os"
    "path/filepath"
    "sort"

    "github.com/terminus/kcompactctl/internal/model"
    "github.com/terminus/kcompactctl/internal/offsetdup"
    "github.com/terminus/kcompactctl/internal/partitionorder"
    "github.com/terminus/kcompactctl/internal/coldstore"
    "github.com/terminus/kcompactctl/internal/tombwin"
)

const (
    findingsPath = "/app/work/segment-audit-report.json"
    genPath      = "/app/state/compact-curator-seal.json"
)

func Run(topic, scenario string) error {
    snap, err := coldstore.ReadStage("")
    if err != nil {
        return err
    }
    findings := analyze(snap.Records)
    if findings == nil {
        findings = []model.Finding{}
    }
    out := model.ReconcileFindings{
        Scenario:     scenario,
        FindingCount: len(findings),
        Findings:     findings,
    }
    if err := writeFindings(out); err != nil {
        return err
    }
    return bumpGeneration()
}

func analyze(records []model.StagedRecord) []model.Finding {
    var findings []model.Finding
    ordered := partitionorder.OrderRecords(records)
    collapsed := offsetdup.Collapse(ordered)

    for i := 1; i < len(collapsed); i++ {
        if collapsed[i].Partition == collapsed[i-1].Partition && collapsed[i].Offset < collapsed[i-1].Offset {
            findings = append(findings, model.Finding{
                Code: "offset_regress", Partition: collapsed[i].Partition,
                Offset: collapsed[i].Offset, Detail: "partition_order_violation",
            })
        }
    }

    dupSeen := map[string]int{}
    for _, rec := range records {
        k := dupKey(rec.Partition, rec.Offset)
        dupSeen[k]++
        if dupSeen[k] > 1 {
            findings = append(findings, model.Finding{
                Code: "dup_offset", Partition: rec.Partition,
                Offset: rec.Offset, Detail: "duplicate_offset_seen",
            })
        }
    }

    window := tombwin.RetentionMs()
    byPart := map[int][]model.StagedRecord{}
    for _, rec := range collapsed {
        byPart[rec.Partition] = append(byPart[rec.Partition], rec)
    }
    for part, partRecs := range byPart {
        hi := tombwin.PartitionHighWater(collapsed, part)
        for _, rec := range partRecs {
            if rec.IsTombstone && !tombwin.TombstoneEligible(rec, hi, window) {
                findings = append(findings, model.Finding{
                    Code: "tomb_expired", Partition: part,
                    Offset: rec.Offset, Detail: "outside_retention_window",
                })
            }
        }
    }

    sort.Slice(findings, func(i, j int) bool {
        if findings[i].Partition != findings[j].Partition {
            return findings[i].Partition < findings[j].Partition
        }
        if findings[i].Offset != findings[j].Offset {
            return findings[i].Offset < findings[j].Offset
        }
        return findings[i].Code < findings[j].Code
    })
    return findings
}

func dupKey(part int, off int64) string {
    return string(rune(part)) + ":" + string(rune(off))
}

func writeFindings(f model.ReconcileFindings) error {
    if err := os.MkdirAll(filepath.Dir(findingsPath), 0o755); err != nil {
        return err
    }
    data, err := json.MarshalIndent(f, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile(findingsPath, data, 0o644)
}

func bumpGeneration() error {
    var gen model.CuratorSealFile
    if raw, err := os.ReadFile(genPath); err == nil {
        _ = json.Unmarshal(raw, &gen)
    }
    gen.CuratorSeal = gen.CuratorSeal
    data, err := json.MarshalIndent(gen, "", "  ")
    if err != nil {
        return err
    }
    data = append(data, '\n')
    return os.WriteFile(genPath, data, 0o644)
}
