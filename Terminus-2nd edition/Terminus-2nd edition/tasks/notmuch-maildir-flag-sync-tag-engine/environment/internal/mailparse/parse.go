package mailparse

import (
	"bytes"
	"net/mail"
	"regexp"
	"strings"
)

var angle = regexp.MustCompile(`<[^>]+>`)

type Parsed struct {
	MessageID  string
	Subject    string
	InReplyTo  string
	References []string
	XKeywords  []string
}

func ParseMessage(data []byte) (Parsed, bool) {
	msg, err := mail.ReadMessage(bytes.NewReader(data))
	if err != nil {
		return Parsed{}, false
	}
	mid := firstAngle(msg.Header.Get("Message-ID"))
	if mid == "" {
		return Parsed{}, false
	}
	p := Parsed{
		MessageID:  mid,
		Subject:    msg.Header.Get("Subject"),
		InReplyTo:  firstAngle(msg.Header.Get("In-Reply-To")),
		References: allAngles(msg.Header.Get("References")),
		XKeywords:  splitKeywords(msg.Header.Get("X-Keywords")),
	}
	return p, true
}

func firstAngle(raw string) string {
	m := angle.FindString(strings.TrimSpace(raw))
	return m
}

func allAngles(raw string) []string {
	return angle.FindAllString(raw, -1)
}

func splitKeywords(raw string) []string {
	if strings.TrimSpace(raw) == "" {
		return nil
	}
	parts := strings.Split(raw, ",")
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		p = strings.ToLower(strings.TrimSpace(p))
		if p != "" {
			out = append(out, p)
		}
	}
	return out
}
