package crashfold

import (
    "crypto/sha256"
    "encoding/hex"
    "fmt"

    "github.com/terminus/coreidx/internal/model"
)

func GroupKey(rec model.CrashRecord, topPC string, buildID, topSymbol string) string {
    h := sha256.New()
    h.Write([]byte(fmt.Sprintf("%d:%s", rec.Signal, topPC)))
    return hex.EncodeToString(h.Sum(nil))
}
