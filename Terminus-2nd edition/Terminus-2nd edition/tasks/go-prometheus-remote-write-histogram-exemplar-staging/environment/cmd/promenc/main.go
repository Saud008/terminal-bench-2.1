package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"

	"promingest/internal/ingest"
	"promingest/internal/model"

	"github.com/golang/snappy"
)

func main() {
	badCRC := flag.Bool("bad-crc", false, "write invalid body checksum")
	flag.Parse()
	if flag.NArg() != 1 {
		fmt.Fprintln(os.Stderr, "usage: promenc [--bad-crc] PAYLOAD.json")
		os.Exit(2)
	}
	data, err := os.ReadFile(flag.Arg(0))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	var req model.WriteRequest
	if err := json.Unmarshal(data, &req); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	out, err := ingest.EncodeWriteBlock(&req)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if *badCRC {
		raw, err := snappy.Decode(nil, out)
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		if len(raw) >= 8 {
			raw[7] ^= 0xFF
		}
		out = snappy.Encode(nil, raw)
	}
	_, _ = os.Stdout.Write(out)
}
