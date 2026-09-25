package persist

import (
	"database/sql"
	"encoding/json"
	"os"

	_ "modernc.org/sqlite"
)

type bindState struct {
	BindPass int `json:"bind_pass"`
}

func Record(id, verb string) error {
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	db, err := sql.Open("sqlite", "/app/state/plate-closure.db")
	if err != nil {
		return err
	}
	defer db.Close()
	if _, err := db.Exec(`CREATE TABLE IF NOT EXISTS lab_events (scenario TEXT, verb TEXT)`); err != nil {
		return err
	}
	_, err = db.Exec(`INSERT INTO lab_events(scenario, verb) VALUES(?, ?)`, id, verb)
	return err
}

func BindPass() int {
	raw, err := os.ReadFile("/app/state/bind-pass.json")
	if err != nil {
		return 0
	}
	var st bindState
	if json.Unmarshal(raw, &st) != nil {
		return 0
	}
	return st.BindPass
}

func Advance() error {
	st := bindState{BindPass: BindPass() + 1}
	if st.BindPass < 1 {
		st.BindPass = 1
	}
	raw, _ := json.Marshal(st)
	return os.WriteFile("/app/state/bind-pass.json", raw, 0o644)
}
