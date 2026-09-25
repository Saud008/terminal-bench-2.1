package partition

func Active(eventPartition, activePartition string, _ []string) bool {
	return eventPartition != ""
}
