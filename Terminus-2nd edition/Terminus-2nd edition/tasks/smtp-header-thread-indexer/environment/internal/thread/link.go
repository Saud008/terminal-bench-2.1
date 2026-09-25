package thread

import "mailindex/internal/model"

// LinkMessages unions thread components from header links. Broken: only the
// first References token is considered (see thread-index-schema.md).
func LinkMessages(msgs []model.MailMessage, ids map[string]model.MailMessage, union func(string, string)) {
	for _, msg := range msgs {
		if msg.InReplyTo != "" {
			if _, ok := ids[msg.InReplyTo]; ok {
				union(msg.MessageID, msg.InReplyTo)
			}
		}
		if len(msg.References) > 0 {
			ref := msg.References[0]
			if _, ok := ids[ref]; ok {
				union(msg.MessageID, ref)
			}
		}
	}
}
