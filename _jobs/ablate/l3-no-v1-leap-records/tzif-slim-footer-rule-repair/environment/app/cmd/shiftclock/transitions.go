package main

import (
	"bufio"
	"flag"
	"fmt"
	"os"

	"shiftclock/internal/civil"
	"shiftclock/internal/report"
)

func runTransitions(args []string) error {
	fs := flag.NewFlagSet("transitions", flag.ContinueOnError)
	zone := fs.String("zone", "", "TZif file or zone name")
	fromYear := fs.Int64("from", 0, "first UTC year (inclusive)")
	toYear := fs.Int64("to", 0, "last UTC year (inclusive)")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if *fromYear == 0 || *toYear == 0 || *toYear < *fromYear {
		return fmt.Errorf("transitions: need --from YEAR --to YEAR with from <= to")
	}
	f, err := openZone(*zone)
	if err != nil {
		return err
	}
	from := civil.DaysFromCivil(*fromYear, 1, 1) * civil.SecondsPerDay
	to := civil.DaysFromCivil(*toYear+1, 1, 1) * civil.SecondsPerDay
	w := bufio.NewWriter(os.Stdout)
	defer w.Flush()
	for _, tr := range f.Transitions(from, to) {
		if err := report.Transition(w, tr); err != nil {
			return err
		}
	}
	return nil
}
