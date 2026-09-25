package indexsql

import (
    "database/sql"
    "encoding/json"
    "os"
    "sort"
    "strings"

    _ "github.com/mattn/go-sqlite3"

    "github.com/terminus/coreidx/internal/model"
)

func Export(staging []model.StagedCrash, sqlitePath, summaryPath string) error {
    if err := os.RemoveAll(sqlitePath); err != nil {
        return err
    }
    db, err := sql.Open("sqlite3", sqlitePath)
    if err != nil {
        return err
    }
    defer db.Close()
    if err := createSchema(db); err != nil {
        return err
    }
    groups := aggregateGroups(staging)
    if err := insertGroups(db, groups); err != nil {
        return err
    }
    if err := insertFrames(db, staging); err != nil {
        return err
    }
    summary := buildSummary(groups)
    b, err := json.MarshalIndent(summary, "", "  ")
    if err != nil {
        return err
    }
    return os.WriteFile(summaryPath, append(b, '\n'), 0o644)
}

func createSchema(db *sql.DB) error {
    _, err := db.Exec(`CREATE TABLE crash_groups (
        group_key TEXT PRIMARY KEY,
        signal INTEGER,
        build_id TEXT,
        top_symbol TEXT,
        crash_count INTEGER
    )`)
    if err != nil {
        return err
    }
    _, err = db.Exec(`CREATE TABLE crash_frames (
        crash_id TEXT,
        group_key TEXT,
        frame_index INTEGER,
        pc TEXT,
        symbol TEXT,
        module TEXT
    )`)
    return err
}

type aggGroup struct {
    model.SummaryGroup
}

func aggregateGroups(staging []model.StagedCrash) []aggGroup {
    counts := map[string]*aggGroup{}
    for _, row := range staging {
        g, ok := counts[row.GroupKey]
        if !ok {
            g = &aggGroup{model.SummaryGroup{
                GroupKey:  row.GroupKey,
                Signal:    row.Signal,
                BuildID:   strings.ToLower(row.BuildID),
                TopSymbol: row.TopSymbol,
            }}
            counts[row.GroupKey] = g
        }
        g.CrashCount++
    }
    out := make([]aggGroup, 0, len(counts))
    for _, g := range counts {
        out = append(out, *g)
    }
    sort.Slice(out, func(i, j int) bool {
        return out[i].GroupKey < out[j].GroupKey
    })
    return out
}

func insertGroups(db *sql.DB, groups []aggGroup) error {
    for _, g := range groups {
        _, err := db.Exec(`INSERT INTO crash_groups (group_key, signal, build_id, top_symbol, crash_count) VALUES (?, ?, ?, ?, ?)`,
            g.GroupKey, g.Signal, g.BuildID, g.TopSymbol, g.CrashCount)
        if err != nil {
            return err
        }
    }
    return nil
}

func insertFrames(db *sql.DB, staging []model.StagedCrash) error {
    for _, row := range staging {
        for i, fr := range row.Frames {
            _, err := db.Exec(`INSERT INTO crash_frames (crash_id, group_key, frame_index, pc, symbol, module) VALUES (?, ?, ?, ?, ?, ?)`,
                row.CrashID, row.GroupKey, i, fr.PC, fr.Symbol, fr.Module)
            if err != nil {
                return err
            }
        }
    }
    return nil
}

func buildSummary(groups []aggGroup) model.Summary {
    sg := make([]model.SummaryGroup, len(groups))
    for i, g := range groups {
        sg[i] = g.SummaryGroup
    }
    return model.Summary{
        Groups: sg,
        Totals: model.SummaryTotals{GroupCount: len(sg)},
    }
}
