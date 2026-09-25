package seal

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"

	"github.com/terminus/termsetctl/internal/journal"
	"github.com/terminus/termsetctl/internal/model"
)

const BundlePath = "/app/output/settlement-bundle.json"
const WitnessPath = "/app/output/settlement-witness.hmac"

func NetAmount(lines []model.JournalLine) (int64, int) {
	var net int64
	settled := 0
	for _, line := range lines {
		switch line.State {
		case "settled":
			net += line.AmountCents
			settled++
		case "reversal_applied":
			net -= line.AmountCents
		}
	}
	return net, settled
}

func WitnessHMAC(keyHex, journalDigest string) (string, error) {
	key, err := hex.DecodeString(keyHex)
	if err != nil {
		return "", err
	}
	mac := hmac.New(sha256.New, key)
	mac.Write([]byte(journalDigest))
	return hex.EncodeToString(mac.Sum(nil)), nil
}

func SealBundle(scenario model.BatchScenario, lines []model.JournalLine) error {
	if err := os.MkdirAll("/app/output", 0o755); err != nil {
		return err
	}
	jDigest := journal.JournalDigest(lines)
	net, settled := NetAmount(lines)
	bundle := model.SettlementBundle{
		Engine:         "termsetctl",
		Scenario:       scenario.Scenario,
		BatchID:        scenario.BatchID,
		TerminalKeyID:  scenario.TerminalKeyID,
		JournalDigest:  jDigest,
		NetAmountCents: net,
		SettledCount:   settled,
		BundleVersion:  1,
	}
	raw, err := json.MarshalIndent(bundle, "", "  ")
	if err != nil {
		return err
	}
	if err := os.WriteFile(BundlePath, raw, 0o644); err != nil {
		return err
	}
	witness, err := WitnessHMAC(scenario.TerminalKeyHex, jDigest)
	if err != nil {
		return err
	}
	return os.WriteFile(WitnessPath, []byte(witness), 0o644)
}

func LoadJournalLines() ([]model.JournalLine, error) {
	raw, err := os.ReadFile(journal.JournalPath)
	if err != nil {
		return nil, err
	}
	lines := []model.JournalLine{}
	for _, chunk := range splitLines(string(raw)) {
		if chunk == "" {
			continue
		}
		var line model.JournalLine
		if err := json.Unmarshal([]byte(chunk), &line); err != nil {
			return nil, err
		}
		lines = append(lines, line)
	}
	return lines, nil
}

func splitLines(s string) []string {
	out := []string{}
	start := 0
	for i := 0; i < len(s); i++ {
		if s[i] == '\n' {
			out = append(out, s[start:i])
			start = i + 1
		}
	}
	if start < len(s) {
		out = append(out, s[start:])
	}
	return out
}

func ReadJournalDigest() (string, error) {
	raw, err := os.ReadFile(journal.JournalMetaPath)
	if err != nil {
		return "", err
	}
	var meta model.JournalFile
	if err := json.Unmarshal(raw, &meta); err != nil {
		return "", err
	}
	return meta.JournalDigest, nil
}

func PublishFromMeta(scenario model.BatchScenario) error {
	lines, err := LoadJournalLines()
	if err != nil {
		return fmt.Errorf("load journal: %w", err)
	}
	return SealBundle(scenario, lines)
}
