package ingest

import (
	"bufio"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"

	"github.com/terminus/fixdropcopy/internal/fixparse"
	"github.com/terminus/fixdropcopy/internal/model"
	"github.com/terminus/fixdropcopy/internal/staging"
)

func Run(seed, scenarioID, fixtureRoot string) error {
	root := fixtureRoot
	if root == "" {
		root = "/app/fixtures"
	}
	manifestPath := filepath.Join(root, "scenarios", scenarioID+".json")
	data, err := os.ReadFile(manifestPath)
	if err != nil {
		return err
	}
	var manifest model.ScenarioFile
	if err := json.Unmarshal(data, &manifest); err != nil {
		return err
	}
	seqBias := 0
	if v := os.Getenv("TB3_SEQ_BIAS"); v != "" {
		seqBias, _ = strconv.Atoi(v)
	}

	var events []model.StageEvent
	hasher := sha256.New()
	for _, rel := range manifest.Streams {
		streamPath := filepath.Join(root, rel)
		hasher.Write([]byte(rel))
		rows, err := loadStream(streamPath, rel, seqBias)
		if err != nil {
			return err
		}
		events = append(events, rows...)
	}
	sort.Slice(events, func(i, j int) bool {
		if events[i].SendingTime == events[j].SendingTime {
			return events[i].MsgSeq < events[j].MsgSeq
		}
		return events[i].SendingTime < events[j].SendingTime
	})

	snap := model.StageSnapshot{
		Engine:       "dropcopy-v1",
		Scenario:     scenarioID,
		EventCount:   len(events),
		Events:       events,
		ReplayGen:    0,
		StreamDigest: hex.EncodeToString(hasher.Sum(nil)),
	}
	if err := staging.WriteStage(staging.DefaultStagePath, snap); err != nil {
		return err
	}

	for _, rel := range manifest.Streams {
		streamPath := filepath.Join(root, rel)
		if _, err := loadStream(streamPath, rel, seqBias); err != nil {
			return err
		}
	}
	return nil
}

func loadStream(path, rel string, seqBias int) ([]model.StageEvent, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var out []model.StageEvent
	sc := bufio.NewScanner(f)
	lineNo := 0
	for sc.Scan() {
		lineNo++
		line := strings.TrimSpace(sc.Text())
		if line == "" {
			continue
		}
		var row model.StreamRow
		if err := json.Unmarshal([]byte(line), &row); err != nil {
			return nil, fmt.Errorf("%s:%d: %w", rel, lineNo, err)
		}
		row.MsgSeq += seqBias
		raw := fixparse.PipeToSOH(row.FixBody)
		ev, ok, err := fixparse.ParseStageEvent(rel, row.Session, row.MsgSeq, row.SendingTime, raw)
		if err != nil {
			return nil, fmt.Errorf("%s:%d: %w", rel, lineNo, err)
		}
		if ok {
			out = append(out, ev)
		}
	}
	return out, sc.Err()
}
