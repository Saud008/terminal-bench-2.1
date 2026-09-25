package main

import (
	"fmt"
	"os"

	"github.com/harbor/ldap-shadow-sync/internal/export"
	"github.com/harbor/ldap-shadow-sync/internal/ingest"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: shadow-sync ingest-ldif|export")
		os.Exit(2)
	}
	switch os.Args[1] {
	case "ingest-ldif":
		if err := ingest.Run(os.Args[2:]); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	case "export":
		if err := export.Run(os.Args[2:]); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	default:
		fmt.Fprintln(os.Stderr, "unknown subcommand")
		os.Exit(2)
	}
}
