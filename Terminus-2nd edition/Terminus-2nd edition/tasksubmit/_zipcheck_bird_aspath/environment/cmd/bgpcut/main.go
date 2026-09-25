package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"bgpcut/pwcore"
)

func usage() {
	fmt.Fprintln(os.Stderr, "usage: bgpcut cutover --scenario <name> --output <path> [--run-id <id>]")
	os.Exit(1)
}

func readSalt() string {
	if v := os.Getenv("TB3_PEER_SALT"); v != "" {
		return v
	}
	b, err := os.ReadFile("/app/config/bgpcut.json")
	if err != nil {
		return ""
	}
	var cfg struct {
		PeerIDSalt string `json:"peer_id_salt"`
	}
	if json.Unmarshal(b, &cfg) != nil {
		return ""
	}
	return cfg.PeerIDSalt
}

func main() {
	if len(os.Args) < 2 || os.Args[1] != "cutover" {
		usage()
	}
	scenario, output, runID := "", "/app/output/bgp_cutover_report.json", "default"
	args := os.Args[2:]
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--scenario":
			if i+1 >= len(args) {
				usage()
			}
			scenario = args[i+1]
			i++
		case "--output":
			if i+1 >= len(args) {
				usage()
			}
			output = args[i+1]
			i++
		case "--run-id":
			if i+1 >= len(args) {
				usage()
			}
			runID = args[i+1]
			i++
		default:
			usage()
		}
	}
	if scenario == "" {
		usage()
	}
	path := filepath.Join("/app/fixtures/peers", scenario, "inventory.json")
	inv, err := pwcore.LoadPeerInventory(path)
	if err != nil {
		if os.IsNotExist(err) {
			fmt.Fprintln(os.Stderr, "missing scenario")
			os.Exit(2)
		}
		fmt.Fprintln(os.Stderr, "invalid inventory")
		os.Exit(3)
	}
	inv = pwcore.ApplyPeerSalt(inv, readSalt())
	led := pwcore.EvaluateCutover(inv, runID)
	_ = os.MkdirAll("/app/state", 0o755)
	lb, _ := json.MarshalIndent(led, "", "  ")
	_ = os.WriteFile("/app/state/cutover-ledger.json", append(lb, '\n'), 0o644)
	rep := pwcore.SealReport(led)
	_ = os.MkdirAll(filepath.Dir(output), 0o755)
	if err := pwcore.WriteSealedReport(output, rep); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(3)
	}
}
