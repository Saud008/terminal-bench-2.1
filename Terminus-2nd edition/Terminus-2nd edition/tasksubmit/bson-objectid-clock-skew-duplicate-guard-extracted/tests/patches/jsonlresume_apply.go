package jsonlresume

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"time"

	"github.com/terminus/wireclock/pkg/intakegate"
	"github.com/terminus/wireclock/pkg/srcursor"
	"github.com/terminus/wireclock/pkg/objclock"
	"github.com/terminus/wireclock/pkg/durastore"
)

type Line struct {
	LineNo    int             `json:"line"`
	NowUnix   int64           `json:"now_unix"`
	MachineID string          `json:"machine_id"`
	ClientSeq int             `json:"client_seq"`
	Payload   json.RawMessage `json:"payload"`
}

type Replayer struct {
	DB        *durastore.DB
	Generator *objclock.Generator
}

func NewReplayer(db *durastore.DB, gen *objclock.Generator) *Replayer {
	return &Replayer{DB: db, Generator: gen}
}

func (r *Replayer) Replay(path string) (int, error) {
	f, err := os.Open(path)
	if err != nil {
		return 0, err
	}
	defer f.Close()

	appliedSet, err := srcursor.LoadAppliedLines(srcursor.ReplayPathCursorPath, path)
	if err != nil {
		return 0, err
	}

	svcCache := map[string]*intakegate.Service{}
	applied := 0
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		var line Line
		if err := json.Unmarshal(sc.Bytes(), &line); err != nil {
			return applied, err
		}
		if _, ok := appliedSet[line.LineNo]; ok {
			continue
		}
		svc, ok := svcCache[line.MachineID]
		if !ok {
			gen := objclock.NewGenerator(line.MachineID)
			gen.BindMachine(line.MachineID)
			svc = intakegate.NewService(r.DB, gen, line.MachineID)
			svcCache[line.MachineID] = svc
		}
		_, err := svc.AdmitBatch(line.NowUnix, []intakegate.Document{{
			ClientSeq: line.ClientSeq,
			Payload:   line.Payload,
		}})
		if err != nil {
			return applied, err
		}
		_, _ = r.DB.SQL.Exec(
			`INSERT INTO resume_applied(resume_path, line_no, applied_at) VALUES(?, ?, ?)`,
			path, line.LineNo, time.Now().Unix(),
		)
		_ = srcursor.RecordApplied(srcursor.ReplayPathCursorPath, path, line.LineNo)
		applied++
	}
	if err := sc.Err(); err != nil {
		return applied, err
	}
	return applied, nil
}

func (r *Replayer) AppliedCount() (int, error) {
	var n int
	err := r.DB.SQL.QueryRow(`SELECT COUNT(*) FROM resume_applied`).Scan(&n)
	return n, err
}

func ValidateLine(raw []byte) (Line, error) {
	var line Line
	if err := json.Unmarshal(raw, &line); err != nil {
		return line, err
	}
	if line.LineNo < 1 || line.MachineID == "" || line.ClientSeq < 1 {
		return line, fmt.Errorf("invalid resume line")
	}
	return line, nil
}
