package bind

// materializeWitnessPayload is the export-stage witness publisher for HTTP 200 JSON.
func materializeWitnessPayload(res Result, snap BindSnapshot) map[string]any {
	payload := map[string]any{"status": "ok", "params": res.Params}
	if res.Body != nil {
		payload["body"] = res.Body
	} else if snap.Body != nil {
		payload["body"] = snap.Body
	}
	return payload
}
