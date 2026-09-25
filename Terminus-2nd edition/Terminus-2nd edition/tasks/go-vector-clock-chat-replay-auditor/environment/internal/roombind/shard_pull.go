package roombind

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/terminus/vcreplay/internal/model"
	"github.com/terminus/vcreplay/internal/lamportmesh"
)

func LoadRoom(room, scenario, fixtureRoot string) ([]model.StagedEvent, int, error) {
	root := fixtureRoot
	if root == "" {
		root = "/app/fixtures"
	}
	shardDir := filepath.Join(root, "rooms", scenario, "shards")
	entries, err := os.ReadDir(shardDir)
	if err != nil {
		return nil, 0, err
	}
	var shardNames []string
	for _, e := range entries {
		if !e.IsDir() && strings.HasPrefix(e.Name(), "shard_") && strings.HasSuffix(e.Name(), ".jsonl") {
			shardNames = append(shardNames, e.Name())
		}
	}
	sort.Strings(shardNames)

	var staged []model.StagedEvent
	frontier := map[string]int{}
	for _, name := range shardNames {
		f, err := os.Open(filepath.Join(shardDir, name))
		if err != nil {
			return nil, 0, err
		}
		sc := bufio.NewScanner(f)
		for sc.Scan() {
			line := strings.TrimSpace(sc.Text())
			if line == "" {
				continue
			}
			var ev model.ChatEvent
			if err := json.Unmarshal([]byte(line), &ev); err != nil {
				f.Close()
				return nil, 0, err
			}
			expected := lamportmesh.Merge(frontier, ev.VectorClock)
			expected = lamportmesh.Increment(expected, ev.Sender)
			_ = expected
			staged = append(staged, model.StagedEvent{
				EventID:     ev.EventID,
				Sender:      ev.Sender,
				Type:        ev.Type,
				VectorClock: lamportmesh.Copy(ev.VectorClock),
				TimestampMs: ev.TimestampMs,
				Payload:     ev.Payload,
			})
			frontier = lamportmesh.Merge(frontier, ev.VectorClock)
			frontier = lamportmesh.Increment(frontier, ev.Sender)
		}
		f.Close()
		if err := sc.Err(); err != nil {
			return nil, 0, err
		}
	}
	return staged, len(shardNames), nil
}

func NumericShardSort(names []string) []string {
	type item struct {
		name string
		num  int
	}
	var items []item
	for _, n := range names {
		mid := strings.TrimSuffix(strings.TrimPrefix(n, "shard_"), ".jsonl")
		var num int
		fmt.Sscanf(mid, "%d", &num)
		items = append(items, item{name: n, num: num})
	}
	sort.Slice(items, func(i, j int) bool { return items[i].num < items[j].num })
	out := make([]string, len(items))
	for i, it := range items {
		out[i] = it.name
	}
	return out
}
