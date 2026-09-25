package weaveloom

import (
    "bufio"
    "encoding/json"
    "fmt"
    "os"
    "sort"
    "time"

    "github.com/terminus/intakectl/internal/holdshield"
    "github.com/terminus/intakectl/internal/kenneldb"
    "github.com/terminus/intakectl/internal/quarcal"
    "github.com/terminus/intakectl/internal/speciesgate"
    "github.com/terminus/intakectl/internal/sheltertypes"
    "github.com/terminus/intakectl/internal/vaccinecheck"
    "github.com/terminus/intakectl/internal/xferpick"
)

func WeaveRun(runID string) error {
    bindPath := fmt.Sprintf("/app/state/intake-bind-%s.json", runID)
    raw, err := os.ReadFile(bindPath)
    if err != nil {
        return err
    }
    var bind sheltertypes.BindArtifact
    if err := json.Unmarshal(raw, &bind); err != nil {
        return err
    }
    db, err := kenneldb.Open(bind.RegistryPath)
    if err != nil {
        return err
    }
    defer db.Close()
    meta, err := kenneldb.ReadMeta(db)
    if err != nil {
        return err
    }
    if v := os.Getenv("TB3_INTAKE_DATE"); v != "" {
        meta.IntakeDate = v
    }
    speciesRows, err := kenneldb.ReadSpecies(db)
    if err != nil {
        return err
    }
    profileMap := map[string]sheltertypes.SpeciesProfile{}
    for _, sp := range speciesRows {
        profileMap[sp.SpeciesCode] = sp
    }
    kennels, err := kenneldb.ReadKennels(db)
    if err != nil {
        return err
    }
    quarantine, err := kenneldb.ReadQuarantine(db)
    if err != nil {
        return err
    }
    arrivals, err := kenneldb.LoadArrivalsJSONL(bind.ArrivalsPath)
    if err != nil {
        return err
    }
    holds, err := kenneldb.ReadHolds(db)
    if err != nil {
        return err
    }
    compatRules, err := kenneldb.ReadCompat(db)
    if err != nil {
        return err
    }
    penalties, err := kenneldb.ReadPenalties(db)
    if err != nil {
        return err
    }
    vaccPolicies, err := kenneldb.ReadVaccination(db)
    if err != nil {
        return err
    }
    scoreMap := map[string]float64{}
    for _, s := range bind.PriorityScores {
        scoreMap[s.IntakeID] = s.PriorityScore
    }
    stamp := bind.RegistryDigest[:16]

    type ranked struct {
        Rec   sheltertypes.IntakeRecord
        Score float64
    }
    var queue []ranked
    for _, rec := range arrivals {
        queue = append(queue, ranked{Rec: rec, Score: scoreMap[rec.IntakeID]})
    }
    sort.SliceStable(queue, func(i, j int) bool {
        if queue[i].Score != queue[j].Score {
            return queue[i].Score > queue[j].Score
        }
        if queue[i].Rec.IntakeRank != queue[j].Rec.IntakeRank {
            return queue[i].Rec.IntakeRank < queue[j].Rec.IntakeRank
        }
        return queue[i].Rec.IntakeID < queue[j].Rec.IntakeID
    })

    usedKennels := map[string]bool{}
    placements := make([]sheltertypes.KennelPlacement, 0)
    transfers := make([]sheltertypes.TransferEntry, 0)

    for _, item := range queue {
        rec := item.Rec
        if !vaccinecheck.VaccineEligible(rec, meta.IntakeDate, vaccPolicies) {
            pick := xferpick.PickTransfer(rec.SpeciesCode, profileMap, compatRules, penalties)
            if pick != nil {
                transfers = append(transfers, sheltertypes.TransferEntry{
                    IntakeID: rec.IntakeID, AnimalID: rec.AnimalID,
                    FromSpecies: rec.SpeciesCode, ToSpecies: pick.ToSpecies,
                    TransferPenalty: pick.TransferPenalty,
                })
            }
            continue
        }
        placed := false
        for _, kennel := range kennels {
            if usedKennels[kennel.KennelID] {
                continue
            }
            if kennel.SpeciesCode != rec.SpeciesCode {
                continue
            }
            if kennel.Capacity <= 0 {
                continue
            }
            if quarcal.KennelQuarantined(kennel.KennelID, meta.IntakeDate, quarantine) {
                continue
            }
            usedKennels[kennel.KennelID] = true
            placements = append(placements, sheltertypes.KennelPlacement{
                IntakeID: rec.IntakeID, AnimalID: rec.AnimalID,
                KennelID: kennel.KennelID, SpeciesCode: kennel.SpeciesCode,
            })
            placed = true
            break
        }
        if placed {
            continue
        }
        for _, kennel := range kennels {
            if usedKennels[kennel.KennelID] {
                continue
            }
            if !speciesgate.AllowedUpgrade(rec.SpeciesCode, kennel.SpeciesCode, profileMap, compatRules) {
                continue
            }
            if kennel.Capacity <= 0 {
                continue
            }
            if quarcal.KennelQuarantined(kennel.KennelID, meta.IntakeDate, quarantine) {
                continue
            }
            usedKennels[kennel.KennelID] = true
            placements = append(placements, sheltertypes.KennelPlacement{
                IntakeID: rec.IntakeID, AnimalID: rec.AnimalID,
                KennelID: kennel.KennelID, SpeciesCode: kennel.SpeciesCode,
            })
            placed = true
            break
        }
        if placed {
            continue
        }
        pick := xferpick.PickTransfer(rec.SpeciesCode, profileMap, compatRules, penalties)
        if pick == nil {
            continue
        }
        transfers = append(transfers, sheltertypes.TransferEntry{
            IntakeID: rec.IntakeID, AnimalID: rec.AnimalID,
            FromSpecies: rec.SpeciesCode, ToSpecies: pick.ToSpecies,
            TransferPenalty: pick.TransferPenalty,
        })
        _ = holdshield.StrongerHold(rec.HoldType, "stray", holds)
        _ = time.Now()
    }

    sort.Slice(placements, func(i, j int) bool { return placements[i].IntakeID < placements[j].IntakeID })
    sort.Slice(transfers, func(i, j int) bool { return transfers[i].IntakeID < transfers[j].IntakeID })

    passPath := fmt.Sprintf("/app/state/weave-pass-%s.json", runID)
    var counter struct {
        WeavePass int    `json:"weave_pass"`
        RunStamp  string `json:"run_stamp"`
    }
    if pr, err := os.ReadFile(passPath); err == nil {
        _ = json.Unmarshal(pr, &counter)
    }
    counter.WeavePass++
    counter.RunStamp = stamp
    passBody, _ := json.Marshal(counter)
    if err := os.WriteFile(passPath, passBody, 0o644); err != nil {
        return err
    }

    if err := os.MkdirAll("/app/work", 0o755); err != nil {
        return err
    }
    jsonlPath := fmt.Sprintf("/app/work/quarantine-weave-%s.jsonl", runID)
    f, err := os.Create(jsonlPath)
    if err != nil {
        return err
    }
    w := bufio.NewWriter(f)
    for _, p := range placements {
        row, _ := json.Marshal(map[string]any{"kind": "placement", "row": p})
        if _, err := w.Write(append(row, '\n')); err != nil {
            f.Close()
            return err
        }
    }
    for _, t := range transfers {
        row, _ := json.Marshal(map[string]any{"kind": "transfer", "row": t})
        if _, err := w.Write(append(row, '\n')); err != nil {
            f.Close()
            return err
        }
    }
    if err := w.Flush(); err != nil {
        f.Close()
        return err
    }
    f.Close()

    header := sheltertypes.WeaveHeader{
        RunID: runID, Scenario: bind.Scenario, Engine: "intakectl",
        RunStamp: stamp, WeavePass: counter.WeavePass,
        Placements: placements, Transfers: transfers,
    }
    headerBody, err := json.Marshal(header)
    if err != nil {
        return err
    }
    headerPath := fmt.Sprintf("/app/work/quarantine-weave-%s.header.json", runID)
    return os.WriteFile(headerPath, headerBody, 0o644)
}
