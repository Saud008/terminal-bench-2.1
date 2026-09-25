package degbridge

import (
    "flag"
    "fmt"
    "os"

    "github.com/terminus/degaudit/internal/audit"
    "github.com/terminus/degaudit/internal/loadscenario"
    "github.com/terminus/degaudit/internal/materialize"
    "github.com/terminus/degaudit/internal/publish"
)

func Dispatch(args []string) error {
    if len(args) == 0 {
        return fmt.Errorf("degaudit: missing subcommand")
    }
    switch args[0] {
    case "load-scenario":
        return runLoad(args[1:])
    case "materialize-transcript":
        return runMaterialize(args[1:])
    case "run-audit":
        return runAudit(args[1:])
    case "publish-report":
        return runPublish(args[1:])
    default:
        return fmt.Errorf("degaudit: unknown subcommand %q", args[0])
    }
}

func runLoad(args []string) error {
    fs := flag.NewFlagSet("load-scenario", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    fixtureDir := fs.String("fixture-dir", "/app/fixtures", "fixture root")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("load-scenario: --scenario required")
    }
    return loadscenario.Load(*fixtureDir, *scenario)
}

func runMaterialize(args []string) error {
    fs := flag.NewFlagSet("materialize-transcript", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("materialize-transcript: --scenario required")
    }
    return materialize.WriteTranscriptMaterial(*scenario)
}

func runAudit(args []string) error {
    fs := flag.NewFlagSet("run-audit", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("run-audit: --scenario required")
    }
    return audit.Run(*scenario)
}

func runPublish(args []string) error {
    fs := flag.NewFlagSet("publish-report", flag.ContinueOnError)
    scenario := fs.String("scenario", "", "scenario name")
    if err := fs.Parse(args); err != nil {
        return err
    }
    if *scenario == "" {
        return fmt.Errorf("publish-report: --scenario required")
    }
    return publish.WriteReport(*scenario)
}

func FixtureDir() string {
    if v := os.Getenv("TB3_FIXTURE_DIR"); v != "" {
        return v
    }
    return "/app/fixtures"
}
