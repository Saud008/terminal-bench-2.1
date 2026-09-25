package main

import (
	"fmt"
	"os"

	syncengine "mailsync/internal/syncengine"
)

func main() {
	if len(os.Args) < 2 {
		usage()
		os.Exit(1)
	}
	switch os.Args[1] {
	case "ingest":
		maildir, db := flagsMaildirDB(2)
		if err := syncengine.Ingest(maildir, db); err != nil {
			fmt.Fprintf(os.Stderr, "ingest: %v\n", err)
			os.Exit(2)
		}
	case "sync":
		maildir, db := flagsMaildirDB(2)
		report := flagValue("--report", "")
		if report == "" {
			usage()
			os.Exit(1)
		}
		if err := syncengine.Sync(maildir, db, report); err != nil {
			fmt.Fprintf(os.Stderr, "sync: %v\n", err)
			os.Exit(2)
		}
	case "publish":
		db := flagValue("--db", "/app/data/mailsync.db")
		report := flagValue("--report", "")
		if report == "" {
			usage()
			os.Exit(1)
		}
		if err := syncengine.Publish(db, report); err != nil {
			fmt.Fprintf(os.Stderr, "publish: %v\n", err)
			os.Exit(2)
		}
	default:
		usage()
		os.Exit(1)
	}
}

func flagsMaildirDB(start int) (string, string) {
	maildir := flagValue("--maildir", "/app/fixtures/maildir")
	if v := os.Getenv("TB3_MAILDIR"); v != "" && v[0] == '/' {
		maildir = v
	}
	db := flagValue("--db", "/app/data/mailsync.db")
	return maildir, db
}

func flagValue(name, def string) string {
	for i := 2; i < len(os.Args); i++ {
		if os.Args[i] == name && i+1 < len(os.Args) {
			return os.Args[i+1]
		}
	}
	return def
}

func usage() {
	fmt.Fprintf(os.Stderr, "usage: mailsync <ingest|sync|publish> [--maildir PATH] [--db PATH] [--report PATH]\n")
}
