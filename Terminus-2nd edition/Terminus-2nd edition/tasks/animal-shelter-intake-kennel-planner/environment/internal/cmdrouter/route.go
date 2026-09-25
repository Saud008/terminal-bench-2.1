package cmdrouter

import (
    "flag"
    "fmt"
    "os"

    "github.com/terminus/intakectl/internal/registrylock"
    "github.com/terminus/intakectl/internal/weaveloom"
    "github.com/terminus/intakectl/internal/sealatlas"
)

func Dispatch(args []string) error {
    if len(args) == 0 {
        return fmt.Errorf("intakectl: missing subcommand")
    }
    switch args[0] {
    case "bind":
        return runBind(args[1:])
    case "weave":
        return runWeave(args[1:])
    case "seal":
        return runSeal(args[1:])
    default:
        return fmt.Errorf("intakectl: unknown subcommand %q", args[0])
    }
}

func runBind(args []string) error {
    fs := flag.NewFlagSet("bind", flag.ContinueOnError)
    registryFmt := fs.String("registry", "", "registry format (sqlite)")
    arrivalsFmt := fs.String("arrivals", "", "arrivals format (jsonl)")
    runID := fs.String("run-id", "", "run identifier")
    scenario := fs.String("scenario", "", "scenario name")
    fixtureDir := fs.String("fixture-dir", "/app/fixtures", "fixture root")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *registryFmt != "sqlite" || *arrivalsFmt != "jsonl" {
        return fmt.Errorf("bind: --registry sqlite and --arrivals jsonl required")
    }
    if *runID == "" || *scenario == "" {
        return fmt.Errorf("bind: --run-id and --scenario required")
    }
    return registrylock.BindRun(*fixtureDir, *scenario, *runID)
}

func runWeave(args []string) error {
    fs := flag.NewFlagSet("weave", flag.ContinueOnError)
    runID := fs.String("run-id", "", "run identifier")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *runID == "" {
        return fmt.Errorf("weave: --run-id required")
    }
    return weaveloom.WeaveRun(*runID)
}

func runSeal(args []string) error {
    fs := flag.NewFlagSet("seal", flag.ContinueOnError)
    runID := fs.String("run-id", "", "run identifier")
    output := fs.String("output", "", "atlas output path")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *runID == "" || *output == "" {
        return fmt.Errorf("seal: --run-id and --output required")
    }
    return sealatlas.SealRun(*runID, *output)
}

func FixtureDir() string {
    if v := os.Getenv("TB3_FIXTURE_DIR"); v != "" {
        return v
    }
    return "/app/fixtures"
}
