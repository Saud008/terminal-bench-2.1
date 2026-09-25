package stagewire

import (
    "crypto/sha256"
    "encoding/hex"
    "strings"

    "github.com/terminus/degaudit/internal/model"
)

func MaterialFingerprint(meta model.ScenarioMeta, courses []model.Course, enrolls []model.Enrollment) string {
    codes := make([]string, 0, len(courses))
    for _, c := range courses {
        codes = append(codes, c.CourseCode)
    }
    parts := append(codes, meta.CatalogSeed)
    payload := strings.Join(parts, "|")
    sum := sha256.Sum256([]byte(payload))
    return hex.EncodeToString(sum[:])
}
