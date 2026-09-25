package fixparse

import (
	"bytes"
	"fmt"
	"strconv"
	"strings"

	"github.com/terminus/fixdropcopy/internal/model"
)

const SOH = byte(0x01)

func PipeToSOH(body string) []byte {
	return []byte(strings.ReplaceAll(body, "|", string(SOH)))
}

func ParseFields(raw []byte) map[string]string {
	out := make(map[string]string)
	start := 0
	for i := 0; i < len(raw); i++ {
		if raw[i] != SOH {
			continue
		}
		if i > start {
			part := string(raw[start:i])
			if eq := strings.IndexByte(part, '='); eq > 0 {
				out[part[:eq]] = part[eq+1:]
			}
		}
		start = i + 1
	}
	if start < len(raw) {
		part := string(raw[start:])
		if eq := strings.IndexByte(part, '='); eq > 0 {
			out[part[:eq]] = part[eq+1:]
		}
	}
	return out
}

func ValidateMessage(msg []byte) error {
	fields := ParseFields(msg)
	raw9, ok := fields["9"]
	if !ok {
		return fmt.Errorf("missing tag 9")
	}
	decl, err := strconv.Atoi(raw9)
	if err != nil {
		return fmt.Errorf("invalid tag 9")
	}
	// FIX BodyLength (tag 9) counts bytes after the BodyLength field's SOH
	// through the SOH immediately preceding CheckSum (tag 10).
	p := bytes.Index(msg, []byte{SOH, '9', '='})
	if p < 0 {
		return fmt.Errorf("missing tag 9")
	}
	sohAfter9 := bytes.IndexByte(msg[p+1:], SOH)
	if sohAfter9 < 0 {
		return fmt.Errorf("missing tag 9")
	}
	bodyStart := p + 1 + sohAfter9 + 1
	bodyEnd := -1
	for j := 0; j < len(msg); j++ {
		if msg[j] == SOH && j+3 < len(msg) && msg[j+1] == '1' && msg[j+2] == '0' && msg[j+3] == '=' {
			bodyEnd = j
			break
		}
	}
	if bodyEnd < 0 {
		return fmt.Errorf("missing checksum")
	}
	actual := bodyEnd - bodyStart + 1
	if decl != actual {
		return fmt.Errorf("body length mismatch")
	}
	got, ok := fields["10"]
	if !ok {
		return fmt.Errorf("missing tag 10")
	}
	want, err := ComputeChecksum(msg)
	if err != nil {
		return err
	}
	if got != want {
		return fmt.Errorf("checksum mismatch")
	}
	return nil
}

func ComputeChecksum(msg []byte) (string, error) {
	idx := bytes.Index(msg, []byte("10="))
	if idx < 0 {
		return "", fmt.Errorf("missing checksum field")
	}
	sum := 0
	for _, b := range msg[:idx] {
		sum += int(b)
	}
	return fmt.Sprintf("%03d", sum%256), nil
}

func ParseStageEvent(streamFile, session string, msgSeq int, sendingTime string, raw []byte) (model.StageEvent, bool, error) {
	if err := ValidateMessage(raw); err != nil {
		return model.StageEvent{}, false, err
	}
	f := ParseFields(raw)
	msgType := f["35"]
	if msgType == "A" && f["141"] == "Y" {
		return model.StageEvent{
			Session:     session,
			MsgSeq:      msgSeq,
			SendingTime: sendingTime,
			ResetSeq:    true,
			StreamFile:  streamFile,
		}, true, nil
	}
	if msgType != "8" {
		return model.StageEvent{}, false, nil
	}
	lastQty, _ := strconv.ParseFloat(f["32"], 64)
	lastPx, _ := strconv.ParseFloat(f["31"], 64)
	ev := model.StageEvent{
		Session:       session,
		MsgSeq:        msgSeq,
		SendingTime:   sendingTime,
		ClOrdID:       f["11"],
		OrigClOrdID:   f["41"],
		ExecID:        f["17"],
		ExecTransType: f["20"],
		ExecType:      f["150"],
		Symbol:        f["55"],
		Side:          f["54"],
		LastQty:       lastQty,
		LastPx:        lastPx,
		StreamFile:    streamFile,
	}
	if ev.ExecID == "" || ev.ClOrdID == "" || ev.Symbol == "" || ev.SendingTime == "" {
		return model.StageEvent{}, false, fmt.Errorf("missing required execution tags")
	}
	if ev.ExecTransType == "" {
		ev.ExecTransType = "0"
	}
	return ev, true, nil
}
