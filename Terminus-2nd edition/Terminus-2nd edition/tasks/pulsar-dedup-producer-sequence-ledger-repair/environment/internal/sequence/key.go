package sequence

// StreamKey identifies a dedup ledger partition.
func StreamKey(producer, topic string) string {
	return producer
}
