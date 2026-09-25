package pipeline

import (
	"strings"
	"time"

	"github.com/terminus/icalexpand/internal/ical"
	"github.com/terminus/icalexpand/internal/model"
	"github.com/terminus/icalexpand/internal/rrule"
	"github.com/terminus/icalexpand/internal/store"
)

func Run(icsPath, window, dbPath string) error {
	start, end, err := parseWindow(window)
	if err != nil {
		return err
	}
	events, zones, err := ical.LoadCalendar(icsPath)
	if err != nil {
		return err
	}
	var all []model.Occurrence
	for _, ev := range events {
		all = append(all, rrule.ExpandEvent(ev, zones, start, end)...)
	}
	st, err := store.Open(dbPath)
	if err != nil {
		return err
	}
	defer st.Close()
	return st.ReplaceAll(all)
}

func parseWindow(raw string) (time.Time, time.Time, error) {
	parts := strings.Split(raw, "/")
	if len(parts) != 2 {
		return time.Time{}, time.Time{}, errBadWindow
	}
	start, err := time.Parse(time.RFC3339, parts[0])
	if err != nil {
		return time.Time{}, time.Time{}, err
	}
	end, err := time.Parse(time.RFC3339, parts[1])
	if err != nil {
		return time.Time{}, time.Time{}, err
	}
	return start.UTC(), end.UTC(), nil
}

var errBadWindow = &windowError{}

type windowError struct{}

func (e *windowError) Error() string { return "invalid --window" }
