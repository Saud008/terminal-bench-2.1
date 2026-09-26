package main

import (
	"flag"
	"fmt"

	"shiftclock/internal/civil"
)

func runInfo(args []string) error {
	fs := flag.NewFlagSet("info", flag.ContinueOnError)
	zone := fs.String("zone", "", "TZif file or zone name")
	if err := fs.Parse(args); err != nil {
		return err
	}
	f, err := openZone(*zone)
	if err != nil {
		return err
	}
	fmt.Printf("version:     %d\n", f.Version)
	fmt.Printf("transitions: %d\n", len(f.Times))
	if n := len(f.Times); n > 0 {
		fmt.Printf("table:       %s .. %s\n", civil.FormatUTC(f.Times[0]), civil.FormatUTC(f.Times[n-1]))
	}
	for i, lt := range f.Types {
		fmt.Printf("type %-2d      offset=%-6d dst=%-5t abbr=%s\n", i, lt.Offset, lt.IsDST, lt.Abbr)
	}
	fmt.Printf("footer:      %q\n", f.Footer)
	return nil
}
