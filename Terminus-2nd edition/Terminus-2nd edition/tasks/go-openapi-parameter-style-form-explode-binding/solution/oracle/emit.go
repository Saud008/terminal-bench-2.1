package bind

// EmitSuccess is the export entrypoint: loads the witness snapshot then publishes HTTP JSON.
func EmitSuccess(res Result) (map[string]any, error) {
	snap, err := ReadBindSnapshot()
	if err != nil {
		return nil, err
	}
	return materializeWitnessPayload(res, snap), nil
}
