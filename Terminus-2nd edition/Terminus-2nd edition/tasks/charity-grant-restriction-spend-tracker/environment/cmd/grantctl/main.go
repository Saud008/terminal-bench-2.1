package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"

	"github.com/terminus/grantctl/internal/compliancekernel"
)

func main() {
	if len(os.Args) < 2 {
		fatalf("usage: grantctl <load-portfolio|apply-amendments|publish-spend-atlas>")
	}
	switch os.Args[1] {
	case "load-portfolio":
		fs := flag.NewFlagSet("load-portfolio", flag.ExitOnError)
		scenario := fs.String("scenario", "", "scenario name")
		fixtureDir := fs.String("fixture-dir", "/app/fixtures", "fixture root")
		_ = fs.Parse(os.Args[2:])
		if *scenario == "" {
			fatalf("missing --scenario")
		}
		if err := compliancekernel.LoadPortfolio(*fixtureDir, *scenario); err != nil {
			fatalf(compliancekernel.ExplainError(err))
		}
	case "apply-amendments":
		if err := compliancekernel.ApplyAmendments(); err != nil {
			fatalf(compliancekernel.ExplainError(err))
		}
	case "publish-spend-atlas":
		atlas, err := compliancekernel.PublishSpendAtlas()
		if err != nil {
			fatalf(compliancekernel.ExplainError(err))
		}
		body, _ := json.Marshal(atlas)
		fmt.Println(string(body))
	default:
		fatalf("unknown subcommand %s", os.Args[1])
	}
}

func fatalf(msg string, args ...any) {
	fmt.Fprintf(os.Stderr, msg+"\n", args...)
	os.Exit(1)
}
