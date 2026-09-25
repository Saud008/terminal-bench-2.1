package seatbridge

import (
    "flag"
    "fmt"
    "os"

    "github.com/terminus/venuetixctl/internal/venueload"
    "github.com/terminus/venuetixctl/internal/seatledger"
    "github.com/terminus/venuetixctl/internal/mapapply"
    "github.com/terminus/venuetixctl/internal/holdfreeze"
)

func Dispatch(args []string) error {
    if len(args) == 0 {
        return fmt.Errorf("venuetixctl: missing subcommand")
    }
    switch args[0] {
    case "load-venue":
        return runLoad(args[1:])
    case "snapshot-holds":
        return runSnapshot(args[1:])
    case "reconcile-map":
        return runReconcile(args[1:])
    case "publish-status":
        return runPublish(args[1:])
    default:
        return fmt.Errorf("venuetixctl: unknown subcommand %q", args[0])
    }
}

func runLoad(args []string) error {
    fs := flag.NewFlagSet("load-venue", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    fixtureDir := fs.String("fixture-dir", "/app/fixtures", "fixture root")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("load-venue: --scenario required")
    }
    if v := os.Getenv("TB3_FIXTURE_DIR"); v != "" {
        *fixtureDir = v
    }
    return loadvenue.Load(*fixtureDir, *scenario)
}

func runSnapshot(args []string) error {
    fs := flag.NewFlagSet("snapshot-holds", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("snapshot-holds: --scenario required")
    }
    return snapshot.WriteHoldSnapshot(*scenario)
}

func runReconcile(args []string) error {
    fs := flag.NewFlagSet("reconcile-map", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("reconcile-map: --scenario required")
    }
    return reconcile.RunMap(*scenario)
}

func runPublish(args []string) error {
    fs := flag.NewFlagSet("publish-status", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("publish-status: --scenario required")
    }
    return publish.WriteStatus(*scenario)
}
