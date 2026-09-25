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
    sort.Slice(transfers, func(i, j int) bool {
        return transfers[i].TransferPenalty > transfers[j].TransferPenalty
    })
    if err := os.MkdirAll("/app/output", 0o755); err != nil {
        return err
    }
    body, err := json.Marshal(map[string]any{
        "scenario": header.Scenario, "engine": "intakectl",
        "run_stamp": header.RunStamp,
        "placements": header.Placements, "transfers": transfers,
    })
    if err != nil {
        return err
    }
    return os.WriteFile(outputPath, body, 0o644)
}
