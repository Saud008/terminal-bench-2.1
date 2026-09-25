package orchestrate

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/platclosectl/internal/bindres"
	"github.com/terminus/platclosectl/internal/cardlex"
	"github.com/terminus/platclosectl/internal/hydrate"
	"github.com/terminus/platclosectl/internal/persist"
	"github.com/terminus/platclosectl/internal/sealcert"
	"github.com/terminus/platclosectl/internal/wcsmatrix"
)

func Run(verb, id, out string) error {
	scenario, err := hydrate.Load(id)
	if err != nil {
		return err
	}
	if err := persist.Record(id, verb); err != nil {
		return err
	}
	if verb == "hydrate-plates" {
		return nil
	}
	plate, err := wcsmatrix.Extract(cardlex.Parse(scenario.HeaderCards))
	if err != nil {
		return err
	}
	rows := bindres.Bind(scenario, plate)
	switch verb {
	case "bind-residuals":
		if err := os.MkdirAll("/app/work/residual-matrix", 0o755); err != nil {
			return err
		}
		path := filepath.Join("/app/work/residual-matrix", id+".jsonl")
		if err := os.WriteFile(path, []byte(bindres.Matrix(scenario, rows)), 0o644); err != nil {
			return err
		}
		return persist.Advance()
	case "seal-closure":
		if persist.BindPass() <= 0 {
			return fmt.Errorf("bind pass required before seal-closure")
		}
		body, err := sealcert.Certificate(id, rows)
		if err != nil {
			return err
		}
		if out == "" {
			out = "/app/output/" + id + "-closure-certificate.json"
		}
		if err := os.MkdirAll(filepath.Dir(out), 0o755); err != nil {
			return err
		}
		return os.WriteFile(out, body, 0o644)
	default:
		return fmt.Errorf("unknown verb %s", verb)
	}
}
