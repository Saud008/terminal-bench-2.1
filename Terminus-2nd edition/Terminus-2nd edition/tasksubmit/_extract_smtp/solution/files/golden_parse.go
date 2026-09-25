package mailparse

import (
	"bytes"
	"mime"
	"net/mail"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"

	"mailindex/internal/model"
)

var angleToken = regexp.MustCompile(`<[^>]+>`)

func LoadMailDir(root string) ([]model.MailMessage, int, int, error) {
	var files []string
	err := filepath.WalkDir(root, func(path string, d os.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if d.IsDir() {
			return nil
		}
		lower := strings.ToLower(d.Name())
		if strings.HasSuffix(lower, ".eml") || strings.HasSuffix(lower, ".mbox") {
			rel, err := filepath.Rel(root, path)
			if err != nil {
				return err
			}
			files = append(files, filepath.ToSlash(rel))
		}
		return nil
	})
	if err != nil {
		return nil, 0, 0, err
	}
	sort.Strings(files)

	var out []model.MailMessage
	skipped := 0
	for fileOrder, rel := range files {
		path := filepath.Join(root, filepath.FromSlash(rel))
		msgs, bad, err := parseMailFile(path, rel, fileOrder)
		if err != nil {
			skipped++
			continue
		}
		skipped += bad
		out = append(out, msgs...)
	}
	return out, len(files), skipped, nil
}

func parseMailFile(path, rel string, fileOrder int) ([]model.MailMessage, int, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, 0, err
	}
	if strings.HasSuffix(strings.ToLower(rel), ".mbox") {
		return parseMbox(data, rel, fileOrder)
	}
	msg, ok := parseEML(data, rel, fileOrder, 0)
	if !ok {
		return nil, 1, nil
	}
	return []model.MailMessage{msg}, 0, nil
}

func parseMbox(data []byte, rel string, fileOrder int) ([]model.MailMessage, int, error) {
	text := strings.ReplaceAll(string(data), "\r\n", "\n")
	parts := splitMbox(text)
	var out []model.MailMessage
	skipped := 0
	for idx, part := range parts {
		part = strings.TrimSpace(part)
		if part == "" {
			continue
		}
		if strings.HasPrefix(part, "From ") {
			if nl := strings.Index(part, "\n"); nl >= 0 {
				part = part[nl+1:]
			}
		}
		msg, ok := parseEML([]byte(part), rel, fileOrder, idx)
		if !ok {
			skipped++
			continue
		}
		out = append(out, msg)
	}
	return out, skipped, nil
}

func splitMbox(text string) []string {
	lines := strings.Split(text, "\n")
	var parts []string
	var cur []string
	for _, line := range lines {
		if strings.HasPrefix(line, "From ") && len(cur) > 0 {
			parts = append(parts, strings.Join(cur, "\n"))
			cur = []string{line}
			continue
		}
		cur = append(cur, line)
	}
	if len(cur) > 0 {
		parts = append(parts, strings.Join(cur, "\n"))
	}
	return parts
}

func parseEML(data []byte, rel string, fileOrder, msgIndex int) (model.MailMessage, bool) {
	msg, err := mail.ReadMessage(bytes.NewReader(data))
	if err != nil {
		return model.MailMessage{}, false
	}
	messageID := normalizeID(firstAngle(msg.Header.Get("Message-ID")))
	if messageID == "" {
		return model.MailMessage{}, false
	}
	dateRaw := msg.Header.Get("Date")
	if dateRaw == "" {
		return model.MailMessage{}, false
	}
	when, err := mail.ParseDate(dateRaw)
	if err != nil {
		return model.MailMessage{}, false
	}
	subject := msg.Header.Get("Subject")
	if subject != "" {
		var decoder mime.WordDecoder
		if decoded, err := decoder.DecodeHeader(subject); err == nil {
			subject = decoded
		}
	}
	inReplyTo := normalizeID(firstAngle(msg.Header.Get("In-Reply-To")))
	refs := parseReferenceIDs(msg.Header.Get("References"))
	return model.MailMessage{
		MessageID:    messageID,
		DateUnix:     when.UTC().Unix(),
		Subject:      subject,
		InReplyTo:    inReplyTo,
		References:   refs,
		SourceFile:   rel,
		FileOrder:    fileOrder,
		MessageIndex: msgIndex,
	}, true
}

func firstAngle(raw string) string {
	raw = strings.TrimSpace(raw)
	match := angleToken.FindString(raw)
	return match
}

func normalizeID(raw string) string {
	return strings.TrimSpace(raw)
}

func parseReferenceIDs(raw string) []string {
	if strings.TrimSpace(raw) == "" {
		return nil
	}
	found := angleToken.FindAllString(raw, -1)
	out := make([]string, 0, len(found))
	for _, tok := range found {
		out = append(out, normalizeID(tok))
	}
	return out
}
