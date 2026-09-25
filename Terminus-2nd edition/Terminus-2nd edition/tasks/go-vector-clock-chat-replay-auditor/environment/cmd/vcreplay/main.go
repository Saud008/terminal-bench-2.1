package main

import (
	"fmt"
	"os"

	"github.com/terminus/vcreplay/internal/vcrcli"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	var err error
	switch os.Args[1] {
	case "load":
		err = runLoad(os.Args[2:])
	case "reconcile":
		err = runReconcile(os.Args[2:])
	case "emit-timeline":
		err = runEmit(os.Args[2:])
	default:
		usage()
		os.Exit(2)
	}
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func usage() {
	fmt.Fprintln(os.Stderr, "vcreplay load --room ROOM --scenario SCENARIO [--fixture-dir D]")
	fmt.Fprintln(os.Stderr, "vcreplay reconcile --room ROOM --scenario SCENARIO")
	fmt.Fprintln(os.Stderr, "vcreplay emit-timeline --room ROOM --scenario SCENARIO [--output PATH]")
}

func runLoad(args []string) error {
	room, scenario, fixtureDir := "", "", "/app/fixtures"
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--room":
			i++
			room = args[i]
		case "--scenario":
			i++
			scenario = args[i]
		case "--fixture-dir":
			i++
			fixtureDir = args[i]
		default:
			return fmt.Errorf("unknown flag %s", args[i])
		}
	}
	if room == "" || scenario == "" {
		return fmt.Errorf("--room and --scenario required")
	}
	snap, err := vcrcli.MaterializeRoom(room, scenario, fixtureDir)
	if err != nil {
		return err
	}
	return vcrcli.PersistStaging(snap)
}

func runReconcile(args []string) error {
	room, scenario := "", ""
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--room":
			i++
			room = args[i]
		case "--scenario":
			i++
			scenario = args[i]
		default:
			return fmt.Errorf("unknown flag %s", args[i])
		}
	}
	_ = room
	if scenario == "" {
		return fmt.Errorf("--scenario required")
	}
	return vcrcli.RunReconcilePass(room, scenario)
}

func runEmit(args []string) error {
	room, scenario, output := "", "", ""
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--room":
			i++
			room = args[i]
		case "--scenario":
			i++
			scenario = args[i]
		case "--output":
			i++
			output = args[i]
		default:
			return fmt.Errorf("unknown flag %s", args[i])
		}
	}
	if room == "" || scenario == "" {
		return fmt.Errorf("--room and --scenario required")
	}
	return vcrcli.SealTimeline(room, scenario, output)
}
