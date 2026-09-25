package bind

// materializeWitnessPayload is the export-stage witness publisher for HTTP 200 JSON.
func materializeWitnessPayload(res Result, snap BindSnapshot) map[string]any {
	payload := map[string]any{"status": "ok", "params": snap.Params}
	if snap.Body != nil {
		payload["body"] = snap.Body
	}
	return payload
}
