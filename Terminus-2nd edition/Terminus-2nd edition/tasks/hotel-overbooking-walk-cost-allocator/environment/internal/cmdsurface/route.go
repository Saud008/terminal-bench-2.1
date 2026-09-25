package cmdsurface

import (
    "flag"
    "fmt"
    "os"

    "github.com/terminus/overbookctl/internal/nightopt"
    "github.com/terminus/overbookctl/internal/revsnap"
    "github.com/terminus/overbookctl/internal/walkreport"
    "github.com/terminus/overbookctl/internal/dbmount"
)

func Dispatch(args []string) error {
    if len(args) == 0 {
        return fmt.Errorf("overbookctl: missing subcommand")
    }
    switch args[0] {
    case "open-database", "ingest-database":
        return runPrime(args[1:])
    case "freeze-capacity-snapshot":
        return runScore(args[1:])
    case "solve-overbook-plan":
        return runAssign(args[1:])
    case "publish-displacement-atlas", "export-displacement-atlas":
        return runEmit(args[1:])
    default:
        return fmt.Errorf("overbookctl: unknown subcommand %q", args[0])
    }
}

func runPrime(args []string) error {
    fs := flag.NewFlagSet("open-database", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    fixtureDir := fs.String("fixture-dir", "/app/fixtures", "fixture root")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("open-database: --scenario required")
    }
    return dbmount.Load(*fixtureDir, *scenario)
}

func runScore(args []string) error {
    fs := flag.NewFlagSet("freeze-capacity-snapshot", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("freeze-capacity-snapshot: --scenario required")
    }
    return revsnap.FreezeSnapshot(*scenario)
}

func runAssign(args []string) error {
    fs := flag.NewFlagSet("solve-overbook-plan", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("solve-overbook-plan: --scenario required")
    }
    return nightopt.RunPlan(*scenario)
}

func runEmit(args []string) error {
    fs := flag.NewFlagSet("publish-displacement-atlas", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("publish-displacement-atlas: --scenario required")
    }
    return walkreport.PublishAtlas(*scenario)
}

func FixtureDir() string {
    if v := os.Getenv("TB3_FIXTURE_DIR"); v != "" {
        return v
    }
    return "/app/fixtures"
}
