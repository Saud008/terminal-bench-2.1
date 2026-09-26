// Package report renders shiftclock results as one JSON object per line.
// Keys are written in a fixed order so output can be diffed across runs.
package report

import (
	"fmt"
	"io"
	"strconv"

	"shiftclock/internal/civil"
	"shiftclock/internal/posixtz"
)

// Instant writes the local time type in effect at t.
func Instant(w io.Writer, t int64, z posixtz.Zone) error {
	_, err := fmt.Fprintf(w, `{"utc":%s,"local":%s,"offset":%d,"abbr":%s,"isdst":%t}`+"\n",
		strconv.Quote(civil.FormatUTC(t)), strconv.Quote(civil.Format(t+z.Offset)), z.Offset, strconv.Quote(z.Abbr), z.IsDST)
	return err
}

// Transition writes one change of local time type.
func Transition(w io.Writer, tr posixtz.Transition) error {
	_, err := fmt.Fprintf(w, `{"at":%s,"offset":%d,"abbr":%s,"isdst":%t}`+"\n",
		strconv.Quote(civil.FormatUTC(tr.At)), tr.Zone.Offset, strconv.Quote(tr.Zone.Abbr), tr.Zone.IsDST)
	return err
}
