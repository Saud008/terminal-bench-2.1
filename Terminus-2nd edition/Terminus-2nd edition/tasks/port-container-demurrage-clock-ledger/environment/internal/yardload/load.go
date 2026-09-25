package yardload

import (
	"os"

	"github.com/terminus/demurctl/internal/clockpass"
	"github.com/terminus/demurctl/internal/fixtureread"
	"github.com/terminus/demurctl/internal/yardsql"
)

func Load(fixtureDir, scenario string) error {
	sc, err := fixtureread.LoadScenario(fixtureDir, scenario)
	if err != nil {
		return err
	}
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return err
	}
	db, err := yardsql.Open(yardsql.YardDB)
	if err != nil {
		return err
	}
	defer db.Close()
	if err := yardsql.InitSchema(db); err != nil {
		return err
	}
	if err := yardsql.ClearYard(db); err != nil {
		return err
	}
	if err := yardsql.InsertScenario(db, sc); err != nil {
		return err
	}
	return clockpass.Reset()
}
