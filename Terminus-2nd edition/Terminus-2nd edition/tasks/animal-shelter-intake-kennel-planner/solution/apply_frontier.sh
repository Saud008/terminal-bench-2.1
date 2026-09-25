#!/usr/bin/env bash
set -euo pipefail
cd /app
sed -i 's/intakeDate < w.EndDate/intakeDate <= w.EndDate/' internal/quarcal/window.go
sed -i 's/return remaining > minDays/return remaining >= minDays/' internal/vaccinecheck/check.go
sed -i 's/return choices\[i\].TransferPenalty > choices\[j\].TransferPenalty/return choices[i].TransferPenalty < choices[j].TransferPenalty/' internal/xferpick/pick.go
sed -i 's/return choices\[i\].ToSpecies > choices\[j\].ToSpecies/return choices[i].ToSpecies < choices[j].ToSpecies/' internal/xferpick/pick.go
sed -i 's/rec.SurrenderProb/(1.0 - rec.SurrenderProb)/' internal/weaveloom/score.go
sed -i 's/return 999/return 50/' internal/holdshield/precedence.go
sed -i 's/HoldPrecedence(aHold, holds) > HoldPrecedence(bHold, holds)/HoldPrecedence(aHold, holds) < HoldPrecedence(bHold, holds)/' internal/holdshield/precedence.go
sed -i 's/to.IsolationRank >= from.IsolationRank/to.IsolationRank > from.IsolationRank/' internal/speciesgate/compat.go

cat > /app/internal/registrylock/digest.go <<'ORACLE_KENNEL_ORACLE_REGISTRYLOCK_DIGEST_GO'
package registrylock

import (
    "crypto/sha256"
    "encoding/hex"
    "fmt"
    "sort"
    "strings"

    "github.com/terminus/intakectl/internal/sheltertypes"
)

func RegistryDigest(meta sheltertypes.ScenarioMeta, kennels []sheltertypes.Kennel, quarantine []sheltertypes.QuarantineWindow) string {
    kennelParts := make([]string, 0, len(kennels))
    for _, k := range kennels {
        kennelParts = append(kennelParts, fmt.Sprintf("%s:%s", k.KennelID, k.SpeciesCode))
    }
    sort.Strings(kennelParts)
    quarParts := make([]string, 0, len(quarantine))
    for _, q := range quarantine {
        quarParts = append(quarParts, fmt.Sprintf("%s:%s:%s", q.KennelID, q.StartDate, q.EndDate))
    }
    sort.Strings(quarParts)
    payload := strings.Join(kennelParts, "|") + "|" + meta.CatalogSeed + "|" + strings.Join(quarParts, "|")
    sum := sha256.Sum256([]byte(payload))
    return hex.EncodeToString(sum[:])
}
ORACLE_KENNEL_ORACLE_REGISTRYLOCK_DIGEST_GO

cat > /app/internal/sealatlas/emit.go <<'ORACLE_KENNEL_ORACLE_SEALATLAS_EMIT_GO'
package sealatlas

import (
    "encoding/json"
    "fmt"
    "os"
    "sort"

    "github.com/terminus/intakectl/internal/sheltertypes"
)

func SealRun(runID, outputPath string) error {
    passPath := fmt.Sprintf("/app/state/weave-pass-%s.json", runID)
    var counter struct {
        WeavePass int `json:"weave_pass"`
    }
    raw, err := os.ReadFile(passPath)
    if err != nil {
        return err
    }
    if err := json.Unmarshal(raw, &counter); err != nil {
        return err
    }
    if counter.WeavePass <= 0 {
        return os.ErrInvalid
    }
    headerPath := fmt.Sprintf("/app/work/quarantine-weave-%s.header.json", runID)
    jsonlPath := fmt.Sprintf("/app/work/quarantine-weave-%s.jsonl", runID)
    headerRaw, err := os.ReadFile(headerPath)
    if err != nil {
        return err
    }
    if _, err := os.ReadFile(jsonlPath); err != nil {
        return err
    }
    var header sheltertypes.WeaveHeader
    if err := json.Unmarshal(headerRaw, &header); err != nil {
        return err
    }
    transfers := header.Transfers
    if transfers == nil {
        transfers = make([]sheltertypes.TransferEntry, 0)
    }
    placements := header.Placements
    if placements == nil {
        placements = make([]sheltertypes.KennelPlacement, 0)
    }
    sort.SliceStable(transfers, func(i, j int) bool {
        if transfers[i].TransferPenalty != transfers[j].TransferPenalty {
            return transfers[i].TransferPenalty < transfers[j].TransferPenalty
        }
        return transfers[i].IntakeID < transfers[j].IntakeID
    })
    if err := os.MkdirAll("/app/output", 0o755); err != nil {
        return err
    }
    body, err := json.Marshal(map[string]any{
        "scenario": header.Scenario, "engine": "intakectl",
        "run_stamp": header.RunStamp,
        "placements": placements, "transfers": transfers,
    })
    if err != nil {
        return err
    }
    return os.WriteFile(outputPath, body, 0o644)
}
ORACLE_KENNEL_ORACLE_SEALATLAS_EMIT_GO

find /app/internal /app/cmd -name '*.go' -exec sed -i 's/\r$//' {} +
