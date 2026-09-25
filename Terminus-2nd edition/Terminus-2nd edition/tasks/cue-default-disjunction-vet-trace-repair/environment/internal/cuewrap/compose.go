package cuewrap

func RunCompose(dir, seed string) (*EvalSnapshot, error) {
	ws, err := LoadWorkspace(dir)
	if err != nil {
		return nil, err
	}
	if IsSnapshotFresh(ws.Name, seed, dir) {
		return ReadEvalSnapshot(EvalSnapshotPath(ws.Name, seed))
	}
	snap := &EvalSnapshot{
		Version:      EvalSnapshotVersion,
		Workspace:    ws.Name,
		Seed:         seed,
		WorkspaceDir: dir,
	}
	if err := DetectEmbedCycle(ws); err != nil {
		snap.OK = false
		snap.Error = err.Error()
		if err := ValidateEvalSnapshot(snap); err != nil {
			return nil, err
		}
		if err := WriteEvalSnapshot(snap); err != nil {
			return nil, err
		}
		return snap, nil
	}
	values, evalErr := EvaluateWorkspace(ws, seed)
	if evalErr != nil {
		snap.OK = false
		snap.Error = evalErr.Error()
		snap.Values = values
		if err := ValidateEvalSnapshot(snap); err != nil {
			return nil, err
		}
		if err := WriteEvalSnapshot(snap); err != nil {
			return nil, err
		}
		return snap, nil
	}
	for _, cfg := range ws.Configs {
		flat, err := FlattenSchema(ws, cfg.Schema)
		if err != nil {
			snap.OK = false
			snap.Error = err.Error()
			snap.Values = values
			if err := ValidateEvalSnapshot(snap); err != nil {
				return nil, err
			}
			if err := WriteEvalSnapshot(snap); err != nil {
				return nil, err
			}
			return snap, nil
		}
		if flat.Closed {
			if err := ValidateClosed(flat, cfg); err != nil {
				snap.OK = false
				snap.Error = err.Error()
				snap.Values = values
				if err := ValidateEvalSnapshot(snap); err != nil {
					return nil, err
				}
				if err := WriteEvalSnapshot(snap); err != nil {
					return nil, err
				}
				return snap, nil
			}
		}
	}
	snap.OK = true
	snap.Values = values
	if err := ValidateEvalSnapshot(snap); err != nil {
		return nil, err
	}
	if err := WriteEvalSnapshot(snap); err != nil {
		return nil, err
	}
	return snap, nil
}
