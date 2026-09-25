package gridrouter

import (
    "flag"
    "fmt"
    "os"

    "github.com/terminus/gridplan/internal/syndemit"
    "github.com/terminus/gridplan/internal/runwaysnap"
    "github.com/terminus/gridplan/internal/syndcompile"
    "github.com/terminus/gridplan/internal/gridimport"
)

func Dispatch(args []string) error {
    if len(args) == 0 {
        return fmt.Errorf("gridplan: missing subcommand")
    }
    switch args[0] {
    case "import-grid":
        return runLoad(args[1:])
    case "snapshot-runway":
        return runMaterialize(args[1:])
    case "compile-windows":
        return runBuild(args[1:])
    case "syndicate-plan":
        return runSyndicate(args[1:])
    default:
        return fmt.Errorf("gridplan: unknown subcommand %q", args[0])
    }
}

func fixtureDir() string {
    if v := os.Getenv("TB3_FIXTURE_DIR"); v != "" {
        return v
    }
    return "/app/fixtures"
}

func runLoad(args []string) error {
    fs := flag.NewFlagSet("import-grid", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    fixtureDirFlag := fs.String("fixture-dir", fixtureDir(), "fixture root")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("import-grid: --scenario required")
    }
    return gridimport.Load(*fixtureDirFlag, *scenario)
}

func runMaterialize(args []string) error {
    fs := flag.NewFlagSet("snapshot-runway", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("snapshot-runway: --scenario required")
    }
    return runwaysnap.WriteRunwaySnap(*scenario)
}

func runBuild(args []string) error {
    fs := flag.NewFlagSet("compile-windows", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("compile-windows: --scenario required")
    }
    return syndcompile.Build(*scenario)
}

func runSyndicate(args []string) error {
    fs := flag.NewFlagSet("syndicate-plan", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("syndicate-plan: --scenario required")
    }
    return syndemit.SyndicatePlan(*scenario)
}
