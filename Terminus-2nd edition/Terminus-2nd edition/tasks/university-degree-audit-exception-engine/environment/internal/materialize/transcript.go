package materialize

import (
    "encoding/json"
    "os"

    "github.com/terminus/degaudit/internal/dbread"
    "github.com/terminus/degaudit/internal/stagewire"
)

const materialPath = "/app/state/transcript-material.json"

func WriteTranscriptMaterial(scenario string) error {
    db, err := dbread.Open("/app/state/registrar-workspace.db")
    if err != nil {
        return err
    }
    defer db.Close()
    meta, err := dbread.ReadMeta(db)
    if err != nil {
        return err
    }
    courses, err := dbread.ReadCourses(db)
    if err != nil {
        return err
    }
    students, err := dbread.ReadStudents(db)
    if err != nil {
        return err
    }
    var enrollCount int
    for _, sid := range students {
        en, err := dbread.ReadEnrollments(db, sid)
        if err != nil {
            return err
        }
        enrollCount += len(en)
        _ = en
    }
    digest := stagewire.MaterialFingerprint(meta, courses, nil)
    body, err := json.Marshal(map[string]any{
        "scenario":           scenario,
        "engine":             "degaudit",
        "material_fingerprint":     digest,
        "course_count":       len(courses),
        "enrollment_count":   enrollCount,
    })
    if err != nil {
        return err
    }
    return os.WriteFile(materialPath, body, 0o644)
}
