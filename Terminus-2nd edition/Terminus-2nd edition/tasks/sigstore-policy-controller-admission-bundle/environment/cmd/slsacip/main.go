// Command slsacip is the Sigstore ClusterImagePolicy attestation admission
// governor CLI.
package main

import (
	"flag"
	"fmt"
	"os"

	"github.com/terminus/slsacip/cipkernel/admitrun"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}

	switch os.Args[1] {
	case "attest":
		if err := runAttest(os.Args[2:]); err != nil {
			fmt.Fprintln(os.Stderr, "slsacip attest:", err)
			os.Exit(1)
		}
	case "-h", "--help", "help":
		usage()
	default:
		fmt.Fprintf(os.Stderr, "slsacip: unknown command %q\n", os.Args[1])
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Fprintln(os.Stderr, "usage: slsacip attest --pulls PULLS.jsonl [--config CONFIG] [--output OUTPUT]")
}

func runAttest(args []string) error {
	fs := flag.NewFlagSet("attest", flag.ContinueOnError)
	cfgPath := fs.String("config", "/app/config/slsacip.json", "path to slsacip config JSON")
	pullsPath := fs.String("pulls", "", "path to the pull request JSONL file (required)")
	outPath := fs.String("output", "/app/output/slsa-admission-ledger.json", "path to write the sealed admission ledger JSON")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if *pullsPath == "" {
		return fmt.Errorf("--pulls is required")
	}
	return admitrun.Run(*cfgPath, *pullsPath, *outPath)
}
