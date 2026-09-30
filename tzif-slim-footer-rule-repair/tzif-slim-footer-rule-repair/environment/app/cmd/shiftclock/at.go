package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"

	"shiftclock/internal/civil"
	"shiftclock/internal/report"
)

func runAt(args []string) error {
	fs := flag.NewFlagSet("at", flag.ContinueOnError)
	zone := fs.String("zone", "", "TZif file or zone name")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if fs.NArg() == 0 {
		return fmt.Errorf("at: no instants given")
	}
	f, err := openZone(*zone)
	if err != nil {
		return err
	}
	instants := make([]int64, 0, fs.NArg())
	for _, s := range fs.Args() {
		t, err := civil.ParseInstant(s)
		if err != nil {
			return err
		}
		instants = append(instants, t)
	}
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	for _, t := range instants {
		if err := report.Instant(w, t, f.Lookup(t)); err != nil {
			return err
		}
	}
	return nil
}
