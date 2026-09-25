package syndcompile

import (
    "encoding/json"
    "os"
    "sort"

    "github.com/terminus/gridplan/internal/model"
    "github.com/terminus/gridplan/internal/runepoch"
    "github.com/terminus/gridplan/internal/plannerdb"
    "github.com/terminus/gridplan/internal/stamp"
    "github.com/terminus/gridplan/internal/windowpick"
)

func Build(scenario string) error {
    bundle, err := readBundle()
    if err != nil {
        return err
    }
    snapRaw, _ := os.ReadFile("/app/state/runway-snapshot.json")
    var runway map[string]any
    _ = json.Unmarshal(snapRaw, &runway)
    digest, _ := runway["runway_digest"].(string)
    runStamp := stamp.ForScenario(scenario, digest)

    programs := append([]model.Program{}, bundle.Programs...)
    sort.SliceStable(programs, func(i, j int) bool {
        if programs[i].StartUTC == programs[j].StartUTC {
            return programs[i].ProgramID < programs[j].ProgramID
        }
        return programs[i].StartUTC < programs[j].StartUTC
    })

    var entries []model.PlanEntry
    var markerAudit []map[string]any
    for _, prog := range programs {
        resolved, markerCount := feedMarkerAudit(prog, bundle)
        airDate := windowpick.AirDate(prog.StartUTC)
        status := airRightsStatus(resolved, bundle.Region, prog.StartUTC, airDate, bundle.Rights, bundle.Blackouts)
        markerAudit = append(markerAudit, map[string]any{
            "program_id": resolved, "marker_count": markerCount,
        })
        entries = append(entries, model.PlanEntry{
            ProgramID: resolved,
            FeedID:    prog.FeedID,
            StartUTC:  prog.StartUTC,
            Region:    bundle.Region,
            Status:    status,
            RunStamp:  runStamp,
        })
    }

    if err := plannerdb.Save(scenario, entries); err != nil {
        return err
    }
    logBody := map[string]any{
        "scenario": scenario, "entry_count": len(entries), "entries": entries, "marker_audit": markerAudit,
    }
    raw, _ := json.MarshalIndent(logBody, "", "  ")
    if err := os.MkdirAll("/app/work", 0o755); err != nil {
        return err
    }
    if err := os.WriteFile("/app/work/window-compile-log.json", append(raw, '\n'), 0o644); err != nil {
        return err
    }
    return runepoch.BumpPlanPass()
}

func readBundle() (*model.ScheduleBundle, error) {
    raw, err := os.ReadFile("/app/state/active-grid.json")
    if err != nil {
        return nil, err
    }
    var bundle model.ScheduleBundle
    if err := json.Unmarshal(raw, &bundle); err != nil {
        return nil, err
    }
    return &bundle, nil
}
