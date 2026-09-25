package sequence

func StreamKey(producer, topic string) string {
	return producer + "|" + topic
}
