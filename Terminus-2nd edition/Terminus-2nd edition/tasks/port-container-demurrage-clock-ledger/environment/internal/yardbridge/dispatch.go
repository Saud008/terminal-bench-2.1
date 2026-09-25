package yardbridge

import (
	"flag"
	"fmt"
	"os"

	"github.com/terminus/demurctl/internal/clockstage"
	"github.com/terminus/demurctl/internal/invoicewriter"
	"github.com/terminus/demurctl/internal/yardload"
)

func Dispatch(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("demurctl: missing subcommand")
	}
	switch args[0] {
	case "load-yard":
		return runLoad(args[1:])
	case "run-dwell-ledger":
		return runDwellLedger(args[1:])
	case "publish-invoices":
		return runPublish(args[1:])
	default:
		return fmt.Errorf("demurctl: unknown subcommand %q", args[0])
	}
}

func runLoad(args []string) error {
	fs := flag.NewFlagSet("load-yard", flag.ContinueOnError)
	scenario := fs.String("scenario", "", "scenario name")
	fixtureDir := fs.String("fixture-dir", "/app/fixtures", "fixture root")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if *scenario == "" {
		return fmt.Errorf("load-yard: --scenario required")
	}
	if v := os.Getenv("TB3_FIXTURE_DIR"); v != "" {
		*fixtureDir = v
	}
	return yardload.Load(*fixtureDir, *scenario)
}

func runDwellLedger(args []string) error {
	fs := flag.NewFlagSet("run-dwell-ledger", flag.ContinueOnError)
	if err := fs.Parse(args); err != nil {
		return err
	}
	return clockstage.Run()
}

func runPublish(args []string) error {
	fs := flag.NewFlagSet("publish-invoices", flag.ContinueOnError)
	if err := fs.Parse(args); err != nil {
		return err
	}
	return invoicewriter.Publish()
}
