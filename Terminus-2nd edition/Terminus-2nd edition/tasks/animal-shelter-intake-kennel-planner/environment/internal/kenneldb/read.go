package kenneldb

import (
    "database/sql"
    "encoding/json"
    "fmt"
    "os"
    "strings"

    _ "modernc.org/sqlite"

    "github.com/terminus/intakectl/internal/sheltertypes"
)

func Open(path string) (*sql.DB, error) {
    db, err := sql.Open("sqlite", path)
    if err != nil {
        return nil, err
    }
    return db, db.Ping()
}

func ReadMeta(db *sql.DB) (sheltertypes.ScenarioMeta, error) {
    var meta sheltertypes.ScenarioMeta
    row := db.QueryRow(`SELECT scenario, intake_date, catalog_seed FROM scenario_meta LIMIT 1`)
    if err := row.Scan(&meta.Scenario, &meta.IntakeDate, &meta.CatalogSeed); err != nil {
        return meta, fmt.Errorf("scenario_meta: %w", err)
    }
    return meta, nil
}

func ReadSpecies(db *sql.DB) ([]sheltertypes.SpeciesProfile, error) {
    rows, err := db.Query(`SELECT species_code, name, isolation_rank FROM species_profiles ORDER BY species_code`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []sheltertypes.SpeciesProfile
    for rows.Next() {
        var sp sheltertypes.SpeciesProfile
        if err := rows.Scan(&sp.SpeciesCode, &sp.Name, &sp.IsolationRank); err != nil {
            return nil, err
        }
        out = append(out, sp)
    }
    return out, rows.Err()
}

func ReadKennels(db *sql.DB) ([]sheltertypes.Kennel, error) {
    rows, err := db.Query(`SELECT kennel_id, species_code, capacity, zone FROM kennels ORDER BY kennel_id`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []sheltertypes.Kennel
    for rows.Next() {
        var k sheltertypes.Kennel
        if err := rows.Scan(&k.KennelID, &k.SpeciesCode, &k.Capacity, &k.Zone); err != nil {
            return nil, err
        }
        out = append(out, k)
    }
    return out, rows.Err()
}

func ReadQuarantine(db *sql.DB) ([]sheltertypes.QuarantineWindow, error) {
    rows, err := db.Query(`SELECT kennel_id, start_date, end_date FROM quarantine_windows ORDER BY kennel_id, start_date`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []sheltertypes.QuarantineWindow
    for rows.Next() {
        var q sheltertypes.QuarantineWindow
        if err := rows.Scan(&q.KennelID, &q.StartDate, &q.EndDate); err != nil {
            return nil, err
        }
        out = append(out, q)
    }
    return out, rows.Err()
}

func ReadVaccination(db *sql.DB) ([]sheltertypes.VaccinationPolicy, error) {
    rows, err := db.Query(`SELECT species_code, min_valid_days FROM vaccination_policies ORDER BY species_code`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []sheltertypes.VaccinationPolicy
    for rows.Next() {
        var p sheltertypes.VaccinationPolicy
        if err := rows.Scan(&p.SpeciesCode, &p.MinValidDays); err != nil {
            return nil, err
        }
        out = append(out, p)
    }
    return out, rows.Err()
}

func ReadCompat(db *sql.DB) ([]sheltertypes.KennelCompatRule, error) {
    rows, err := db.Query(`SELECT from_species, to_species FROM kennel_compat_rules ORDER BY from_species, to_species`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []sheltertypes.KennelCompatRule
    for rows.Next() {
        var r sheltertypes.KennelCompatRule
        if err := rows.Scan(&r.FromSpecies, &r.ToSpecies); err != nil {
            return nil, err
        }
        out = append(out, r)
    }
    return out, rows.Err()
}

func ReadPenalties(db *sql.DB) ([]sheltertypes.TransferPenalty, error) {
    rows, err := db.Query(`SELECT from_species, to_species, transfer_penalty FROM transfer_penalties ORDER BY from_species, to_species`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []sheltertypes.TransferPenalty
    for rows.Next() {
        var tp sheltertypes.TransferPenalty
        if err := rows.Scan(&tp.FromSpecies, &tp.ToSpecies, &tp.TransferPenalty); err != nil {
            return nil, err
        }
        out = append(out, tp)
    }
    return out, rows.Err()
}

func ReadHolds(db *sql.DB) ([]sheltertypes.AdoptionHold, error) {
    rows, err := db.Query(`SELECT hold_type, precedence_rank FROM adoption_holds ORDER BY precedence_rank, hold_type`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []sheltertypes.AdoptionHold
    for rows.Next() {
        var h sheltertypes.AdoptionHold
        if err := rows.Scan(&h.HoldType, &h.PrecedenceRank); err != nil {
            return nil, err
        }
        out = append(out, h)
    }
    return out, rows.Err()
}

func LoadArrivalsJSONL(path string) ([]sheltertypes.IntakeRecord, error) {
    raw, err := os.ReadFile(path)
    if err != nil {
        return nil, err
    }
    var out []sheltertypes.IntakeRecord
    for _, line := range strings.Split(strings.TrimSpace(string(raw)), "\n") {
        if line == "" {
            continue
        }
        var rec sheltertypes.IntakeRecord
        if err := json.Unmarshal([]byte(line), &rec); err != nil {
            return nil, err
        }
        out = append(out, rec)
    }
    return out, nil
}
