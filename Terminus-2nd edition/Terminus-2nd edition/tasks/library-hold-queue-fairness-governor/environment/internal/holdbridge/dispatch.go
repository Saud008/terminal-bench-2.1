package holdbridge

import (
    "flag"
    "fmt"
    "os"

    "github.com/terminus/holdfairctl/internal/loadscenario"
    "github.com/terminus/holdfairctl/internal/materialize"
    "github.com/terminus/holdfairctl/internal/atlasledger"
    "github.com/terminus/holdfairctl/internal/reconcile"
)

func Dispatch(args []string) error {
    if len(args) == 0 {
        return fmt.Errorf("holdfairctl: missing subcommand")
    }
    switch args[0] {
            case "mount-library-db":
                return runLoad(args[1:])
            case "compose-rollup":
                return runMaterialize(args[1:])
            case "rank-fair-holds":
                return runReconcile(args[1:])
            case "write-assignment-atlas":
                return runPublish(args[1:])
    default:
        return fmt.Errorf("holdfairctl: unknown subcommand %q", args[0])
    }
}

func runLoad(args []string) error {
    fs := flag.NewFlagSet("mount-library-db", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    fixtureDir := fs.String("fixture-dir", "/app/fixtures", "fixture root")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("mount-library-db: --scenario required")
    }
    return loadscenario.Load(*fixtureDir, *scenario)
}

func runMaterialize(args []string) error {
    fs := flag.NewFlagSet("compose-rollup", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("compose-rollup: --scenario required")
    }
    return materialize.WriteQueueRollup(*scenario)
}

func runReconcile(args []string) error {
    fs := flag.NewFlagSet("rank-fair-holds", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("rank-fair-holds: --scenario required")
    }
    return reconcile.RunFairness(*scenario)
}

func runPublish(args []string) error {
    fs := flag.NewFlagSet("write-assignment-atlas", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("write-assignment-atlas: --scenario required")
    }
    return atlasledger.WriteAtlas(*scenario)
}

func FixtureDir() string {
    if v := os.Getenv("TB3_FIXTURE_DIR"); v != "" {
        return v
    }
    return "/app/fixtures"
}
