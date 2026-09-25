package dbread

import (
    "database/sql"
    "fmt"

    _ "modernc.org/sqlite"

    "github.com/terminus/degaudit/internal/model"
)

func Open(path string) (*sql.DB, error) {
    db, err := sql.Open("sqlite", path)
    if err != nil {
        return nil, err
    }
    return db, db.Ping()
}

func ReadMeta(db *sql.DB) (model.ScenarioMeta, error) {
    var meta model.ScenarioMeta
    row := db.QueryRow(`SELECT scenario, audit_date, catalog_year, audit_term, catalog_seed FROM scenario_meta LIMIT 1`)
    if err := row.Scan(&meta.Scenario, &meta.AuditDate, &meta.CatalogYear, &meta.AuditTerm, &meta.CatalogSeed); err != nil {
        return meta, fmt.Errorf("scenario_meta: %w", err)
    }
    return meta, nil
}

func ReadCourses(db *sql.DB) ([]model.Course, error) {
    rows, err := db.Query(`SELECT course_code, title, credits, catalog_year FROM courses ORDER BY course_code`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.Course
    for rows.Next() {
        var c model.Course
        if err := rows.Scan(&c.CourseCode, &c.Title, &c.Credits, &c.CatalogYear); err != nil {
            return nil, err
        }
        out = append(out, c)
    }
    return out, rows.Err()
}

func ReadEnrollments(db *sql.DB, studentID string) ([]model.Enrollment, error) {
    rows, err := db.Query(`SELECT student_id, course_code, term, grade_points, is_transfer FROM enrollments WHERE student_id = ? ORDER BY course_code, term`, studentID)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.Enrollment
    for rows.Next() {
        var e model.Enrollment
        var xfer int
        if err := rows.Scan(&e.StudentID, &e.CourseCode, &e.Term, &e.GradePoints, &xfer); err != nil {
            return nil, err
        }
        e.IsTransfer = xfer != 0
        out = append(out, e)
    }
    return out, rows.Err()
}

func ReadTransferEquiv(db *sql.DB) ([]model.TransferEquiv, error) {
    rows, err := db.Query(`SELECT source_code, target_code, valid_from_year, valid_to_year FROM transfer_equiv ORDER BY source_code`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.TransferEquiv
    for rows.Next() {
        var t model.TransferEquiv
        if err := rows.Scan(&t.SourceCode, &t.TargetCode, &t.ValidFromYear, &t.ValidToYear); err != nil {
            return nil, err
        }
        out = append(out, t)
    }
    return out, rows.Err()
}

func ReadSubstitutions(db *sql.DB) ([]model.Substitution, error) {
    rows, err := db.Query(`SELECT sub_req_id, replaces_req_id, expires_after_term FROM substitutions ORDER BY sub_req_id`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.Substitution
    for rows.Next() {
        var s model.Substitution
        if err := rows.Scan(&s.SubReqID, &s.ReplacesReqID, &s.ExpiresAfterTerm); err != nil {
            return nil, err
        }
        out = append(out, s)
    }
    return out, rows.Err()
}

func ReadRequirements(db *sql.DB) ([]model.Requirement, error) {
    rows, err := db.Query(`SELECT req_id, parent_req_id, required_credits FROM requirements ORDER BY req_id`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.Requirement
    for rows.Next() {
        var r model.Requirement
        if err := rows.Scan(&r.ReqID, &r.ParentReqID, &r.RequiredCredits); err != nil {
            return nil, err
        }
        out = append(out, r)
    }
    return out, rows.Err()
}

func ReadRequirementCourses(db *sql.DB) ([]model.RequirementCourse, error) {
    rows, err := db.Query(`SELECT req_id, course_code FROM requirement_courses ORDER BY req_id, course_code`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.RequirementCourse
    for rows.Next() {
        var rc model.RequirementCourse
        if err := rows.Scan(&rc.ReqID, &rc.CourseCode); err != nil {
            return nil, err
        }
        out = append(out, rc)
    }
    return out, rows.Err()
}

func ReadWaivers(db *sql.DB, studentID string) ([]model.Waiver, error) {
    rows, err := db.Query(`SELECT student_id, req_id, reason FROM waivers WHERE student_id = ? ORDER BY req_id`, studentID)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []model.Waiver
    for rows.Next() {
        var w model.Waiver
        if err := rows.Scan(&w.StudentID, &w.ReqID, &w.Reason); err != nil {
            return nil, err
        }
        out = append(out, w)
    }
    return out, rows.Err()
}

func ReadStudents(db *sql.DB) ([]string, error) {
    rows, err := db.Query(`SELECT student_id FROM students ORDER BY student_id`)
    if err != nil {
        return nil, err
    }
    defer rows.Close()
    var out []string
    for rows.Next() {
        var id string
        if err := rows.Scan(&id); err != nil {
            return nil, err
        }
        out = append(out, id)
    }
    return out, rows.Err()
}
