package main

import (
	"encoding/json"
	"fmt"
	"os"

	"vtgatesim/internal/cache"
	"vtgatesim/internal/export"
	"vtgatesim/internal/ingest"
	"vtgatesim/internal/migration"
	"vtgatesim/internal/model"
	"vtgatesim/internal/route"
	"vtgatesim/internal/staging"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(2)
	}
	switch os.Args[1] {
	case "ingest":
		runIngest()
	case "route":
		runRoute()
	case "export":
		runExport()
	case "migrate":
		runMigrate()
	default:
		usage()
		os.Exit(2)
	}
}

func usage() {
	fmt.Fprintln(os.Stderr, "usage: vtgatesim ingest|route|export|migrate ...")
}

func runIngest() {
	shardMap, vindexes, snapshot := "", "", ""
	cacheSeed := ""
	for i := 2; i < len(os.Args); i++ {
		switch os.Args[i] {
		case "--shard-map":
			i++
			shardMap = os.Args[i]
		case "--vindexes":
			i++
			vindexes = os.Args[i]
		case "--snapshot":
			i++
			snapshot = os.Args[i]
		case "--cache-seed":
			i++
			cacheSeed = os.Args[i]
		default:
			os.Exit(2)
		}
	}
	if shardMap == "" || vindexes == "" || snapshot == "" {
		os.Exit(2)
	}
	var seed []model.CacheEntry
	if cacheSeed != "" {
		data, err := os.ReadFile(cacheSeed)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		if err := json.Unmarshal(data, &seed); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	}
	if err := ingest.Run(shardMap, vindexes, snapshot, seed); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func runRoute() {
	snapshot, batch, out := "", "", ""
	for i := 2; i < len(os.Args); i++ {
		switch os.Args[i] {
		case "--snapshot":
			i++
			snapshot = os.Args[i]
		case "--batch":
			i++
			batch = os.Args[i]
		case "--output":
			i++
			out = os.Args[i]
		default:
			os.Exit(2)
		}
	}
	if snapshot == "" || batch == "" || out == "" {
		os.Exit(2)
	}
	plan, err := route.Run(snapshot, batch)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	data, err := json.MarshalIndent(plan, "", "  ")
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := os.WriteFile(out, data, 0o644); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func runExport() {
	snapshot, planPath, auditOut := "", "", ""
	for i := 2; i < len(os.Args); i++ {
		switch os.Args[i] {
		case "--snapshot":
			i++
			snapshot = os.Args[i]
		case "--plan":
			i++
			planPath = os.Args[i]
		case "--audit-out":
			i++
			auditOut = os.Args[i]
		default:
			os.Exit(2)
		}
	}
	if snapshot == "" || planPath == "" || auditOut == "" {
		os.Exit(2)
	}
	planData, err := os.ReadFile(planPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	var plan model.RoutePlan
	if err := json.Unmarshal(planData, &plan); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	audit, err := export.BuildAudit(snapshot, plan)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := export.WriteAudit(auditOut, audit); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func runMigrate() {
	eventsPath, snapshot := "", ""
	for i := 2; i < len(os.Args); i++ {
		switch os.Args[i] {
		case "--events":
			i++
			eventsPath = os.Args[i]
		case "--snapshot":
			i++
			snapshot = os.Args[i]
		default:
			os.Exit(2)
		}
	}
	if eventsPath == "" || snapshot == "" {
		os.Exit(2)
	}
	snap, err := staging.ReadSnapshot(snapshot)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	events, err := loadEvents(eventsPath)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	store := cache.NewStore(snap.Cache)
	for _, ev := range events {
		if err := migration.ApplyEvent(store, &snap, ev); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	}
	snap.Cache = store.Entries()
	if err := staging.WriteSnapshot(snapshot, snap); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func loadEvents(path string) ([]model.MigrationEvent, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var events []model.MigrationEvent
	for _, line := range splitLines(string(data)) {
		if line == "" {
			continue
		}
		var ev model.MigrationEvent
		if err := json.Unmarshal([]byte(line), &ev); err != nil {
			return nil, err
		}
		events = append(events, ev)
	}
	return events, nil
}

func splitLines(s string) []string {
	var out []string
	start := 0
	for i := 0; i < len(s); i++ {
		if s[i] == '\n' {
			out = append(out, trimLine(s[start:i]))
			start = i + 1
		}
	}
	if start < len(s) {
		out = append(out, trimLine(s[start:]))
	}
	return out
}

func trimLine(s string) string {
	for len(s) > 0 && (s[0] == ' ' || s[0] == '\t' || s[0] == '\r') {
		s = s[1:]
	}
	for len(s) > 0 && (s[len(s)-1] == ' ' || s[len(s)-1] == '\t' || s[len(s)-1] == '\r') {
		s = s[:len(s)-1]
	}
	return s
}
