// Command shiftclock answers local-time questions for the rostering service
// straight from compiled TZif files, so that on-call handover times do not
// depend on whatever tzdata the host happens to have installed.
package main

import (
	"fmt"
	"os"
	"path/filepath"

	"shiftclock/internal/tzif"
)

const defaultZoneDir = "/app/zones"

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	var err error
	switch os.Args[1] {
	case "at":
		err = runAt(os.Args[2:])
	case "transitions":
		err = runTransitions(os.Args[2:])
	case "info":
		err = runInfo(os.Args[2:])
	case "-h", "--help", "help":
		usage()
		return
	default:
		usage()
		os.Exit(2)
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, "shiftclock:", err)
		os.Exit(1)
	}
}

func usage() {
	fmt.Fprint(os.Stderr, `usage:
  shiftclock at --zone ZONE INSTANT...
  shiftclock transitions --zone ZONE --from YEAR --to YEAR
  shiftclock info --zone ZONE

ZONE is a path to a TZif file, or a name looked up under $SHIFTCLOCK_ZONEINFO
(default /app/zones). INSTANT is Unix seconds or YYYY-MM-DDTHH:MM:SSZ.
`)
}

// openZone resolves a --zone argument and loads the file.
func openZone(zone string) (*tzif.File, error) {
	if zone == "" {
		return nil, fmt.Errorf("--zone is required")
	}
	path := zone
	if _, err := os.Stat(zone); err != nil && !filepath.IsAbs(zone) {
		dir := os.Getenv("SHIFTCLOCK_ZONEINFO")
		if dir == "" {
			dir = defaultZoneDir
		}
		path = filepath.Join(dir, zone)
	}
	return tzif.Load(path)
}
