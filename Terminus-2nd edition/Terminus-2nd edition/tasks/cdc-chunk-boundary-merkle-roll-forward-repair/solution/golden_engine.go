package roll

import (
	"encoding/json"
	"os"
	"path/filepath"

	"github.com/terminus/cdcctl/internal/chunk"
	"github.com/terminus/cdcctl/internal/checkpoint"
	"github.com/terminus/cdcctl/internal/config"
	"github.com/terminus/cdcctl/internal/merkle"
	"github.com/terminus/cdcctl/internal/model"
)

type Options struct {
	InputPath      string
	Seed           string
	OutputPath     string
	CheckpointPath string
	Resume         bool
	MaxChunks      int
}

func Roll(opts Options) (model.RollReport, error) {
	data, err := os.ReadFile(opts.InputPath)
	if err != nil {
		return model.RollReport{}, err
	}
	p := config.ForSeed(opts.Seed)
	source := filepath.Base(opts.InputPath)

	var cp model.Checkpoint
	resumed := false
	rt := chunk.NewRuntime(0, nil)
	var chunks []model.ChunkRecord
	var leaves []string
	startPos := 0

	if opts.Resume {
		cp, err = checkpoint.Load(opts.CheckpointPath)
		if err != nil {
			return model.RollReport{}, err
		}
		if cp.Source != source || cp.Seed != opts.Seed {
			return model.RollReport{}, os.ErrInvalid
		}
		resumed = true
		chunks = append(chunks, cp.Chunks...)
		leaves = append(leaves, cp.Leaves...)
		rt = checkpoint.RuntimeFrom(cp)
		startPos = cp.Offset
	}

	newChunks := 0
	for pos := startPos; pos < len(data); pos++ {
		if rec := rt.Feed(data, pos, opts.Seed, p); rec != nil {
			chunks = append(chunks, *rec)
			leaves = append(leaves, rec.Hash)
			newChunks++
			if opts.MaxChunks > 0 && newChunks >= opts.MaxChunks {
				cp = model.Checkpoint{
					Source:     source,
					Seed:       opts.Seed,
					Offset:     pos + 1,
					ChunkStart: rt.ChunkStart,
					Window:     checkpoint.EncodeWindow(rt.Window),
					Chunks:     chunks,
					Leaves:     leaves,
					Complete:   false,
				}
				if err := checkpoint.Save(opts.CheckpointPath, cp); err != nil {
					return model.RollReport{}, err
				}
				return model.RollReport{}, nil
			}
		}
	}

	report := model.RollReport{
		Source:     source,
		Seed:       opts.Seed,
		BytesTotal: len(data),
		ChunkCount: len(chunks),
		MerkleRoot: merkle.Root(leaves),
		Resumed:    resumed,
		Chunks:     chunks,
	}
	if opts.OutputPath != "" {
		out, err := json.MarshalIndent(report, "", "  ")
		if err != nil {
			return model.RollReport{}, err
		}
		if err := os.WriteFile(opts.OutputPath, out, 0o644); err != nil {
			return model.RollReport{}, err
		}
	}
	cp = model.Checkpoint{
		Source:     source,
		Seed:       opts.Seed,
		Offset:     len(data),
		ChunkStart: rt.ChunkStart,
		Window:     checkpoint.EncodeWindow(rt.Window),
		Chunks:     chunks,
		Leaves:     leaves,
		Complete:   true,
	}
	if opts.CheckpointPath != "" {
		if err := checkpoint.Save(opts.CheckpointPath, cp); err != nil {
			return model.RollReport{}, err
		}
	}
	return report, nil
}
