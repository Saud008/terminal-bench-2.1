package thread

import "mailindex/internal/model"

func LinkMessages(msgs []model.MailMessage, ids map[string]model.MailMessage, union func(string, string)) {
	for _, msg := range msgs {
		if msg.InReplyTo != "" {
			if _, ok := ids[msg.InReplyTo]; ok {
				union(msg.MessageID, msg.InReplyTo)
			}
		}
		for _, ref := range msg.References {
			if _, ok := ids[ref]; ok {
				union(msg.MessageID, ref)
			}
		}
	}
}
