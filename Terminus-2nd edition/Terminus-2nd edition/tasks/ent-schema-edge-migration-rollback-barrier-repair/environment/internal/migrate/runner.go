package migrate

import (
	"database/sql"
	"fmt"
	"strings"

	"github.com/terminus/ent-migrate/internal/codegen"
	"github.com/terminus/ent-migrate/internal/db"
	"github.com/terminus/ent-migrate/internal/model"
)

func RunUp(conn *sql.DB, cat *model.Catalog) (*model.Report, error) {
	plan := PlanUp()
	report := &model.Report{Direction: "up", Events: []model.ReportEvent{}}
	seq := 0
	addEvent := func(p phase) {
		seq++
		report.Events = append(report.Events, model.ReportEvent{Phase: string(p), Seq: seq})
	}

	for _, step := range plan {
		switch step {
		case phaseCodegen:
			hash, err := codegen.Refresh(cat)
			if err != nil {
				return nil, err
			}
			report.CodegenHash = hash
			addEvent(step)
		case phaseSnapshot:
			snap, err := TakeSnapshot(conn, report.CodegenHash)
			if err != nil {
				return nil, err
			}
			report.SnapshotSeq = snap
			addEvent(step)
		case phasePreValidate, phasePostValidate:
			if err := RunHook(conn, step); err != nil {
				return nil, err
			}
			addEvent(step)
		case phaseBackfill:
			if err := BackfillAuthor(conn); err != nil {
				return nil, err
			}
			addEvent(step)
		case phaseAddFK:
			if err := AttachEdgeFK(conn); err != nil {
				return nil, err
			}
			addEvent(step)
		default:
			if err := ApplyPhaseSQL(conn, cat, step); err != nil {
				return nil, err
			}
			addEvent(step)
		}
	}

	orphans, err := db.CountOrphanAuthors(conn)
	if err != nil {
		return nil, err
	}
	if orphans > 0 {
		return nil, fmt.Errorf("orphan author_id rows remain: %d", orphans)
	}
	posts, err := db.CountPosts(conn)
	if err != nil {
		return nil, err
	}
	report.SchemaVersion = cat.TargetVersion
	report.Counts = model.ReportCounts{Posts: posts, Orphans: orphans}
	if err := db.SetSchemaVersion(conn, cat.TargetVersion); err != nil {
		return nil, err
	}
	return report, nil
}

func RunDown(conn *sql.DB, cat *model.Catalog, steps int) (*model.Report, error) {
	plan := PlanDown()
	if steps <= 0 || steps > len(plan) {
		return nil, fmt.Errorf("invalid down steps %d", steps)
	}
	report := &model.Report{Direction: "down", Events: []model.ReportEvent{}}
	seq := 0
	for i := 0; i < steps; i++ {
		step := plan[i]
		if err := ApplyPhaseSQL(conn, cat, step); err != nil {
			return nil, err
		}
		seq++
		report.Events = append(report.Events, model.ReportEvent{Phase: string(step), Seq: seq})
	}
	v, err := db.DetectSchemaVersion(conn)
	if err != nil {
		return nil, err
	}
	if err := db.SetSchemaVersion(conn, v); err != nil {
		return nil, err
	}
	report.SchemaVersion = v
	return report, nil
}

func ApplyPhaseSQL(conn *sql.DB, cat *model.Catalog, step phase) error {
	sqlText, ok := cat.SQL[string(step)]
	if !ok {
		return fmt.Errorf("missing sql for %s", step)
	}
	for _, stmt := range splitStatements(sqlText) {
		if _, err := conn.Exec(stmt); err != nil {
			return err
		}
	}
	return nil
}

func splitStatements(sqlText string) []string {
	parts := strings.Split(sqlText, ";")
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			out = append(out, p)
		}
	}
	return out
}
