package cmdrouter

import (
    "flag"
    "fmt"
    "os"

    "github.com/terminus/ttalloc/internal/rosterload"
    "github.com/terminus/ttalloc/internal/constraintgraph"
    "github.com/terminus/ttalloc/internal/slotplan"
    "github.com/terminus/ttalloc/internal/timetablepub"
)

func Dispatch(args []string) error {
    if len(args) == 0 {
        return fmt.Errorf("ttalloc: missing subcommand")
    }
    switch args[0] {
    case "load-roster":
        return runLoad(args[1:])
    case "materialize-graph":
        return runMaterialize(args[1:])
    case "allocate-slots":
        return runAllocate(args[1:])
    case "publish-atlas":
        return runPublish(args[1:])
    default:
        return fmt.Errorf("ttalloc: unknown subcommand %q", args[0])
    }
}

func fixtureDir() string {
    if v := os.Getenv("TB3_FIXTURE_DIR"); v != "" {
        return v
    }
    return "/app/fixtures"
}

func runLoad(args []string) error {
    fs := flag.NewFlagSet("load-roster", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    fixtureDirFlag := fs.String("fixture-dir", fixtureDir(), "fixture root")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("load-roster: --scenario required")
    }
    return rosterload.LoadBundle(*fixtureDirFlag, *scenario)
}

func runMaterialize(args []string) error {
    fs := flag.NewFlagSet("materialize-graph", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("materialize-graph: --scenario required")
    }
    return constraintgraph.WriteGraph(*scenario)
}

func runAllocate(args []string) error {
    fs := flag.NewFlagSet("allocate-slots", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("allocate-slots: --scenario required")
    }
    return slotplan.RunPlan(*scenario)
}

func runPublish(args []string) error {
    fs := flag.NewFlagSet("publish-atlas", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("publish-atlas: --scenario required")
    }
    return timetablepub.Publish(*scenario)
}
