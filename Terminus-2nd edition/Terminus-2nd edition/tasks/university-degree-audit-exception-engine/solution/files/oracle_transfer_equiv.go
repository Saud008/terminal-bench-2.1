package transmap

import "github.com/terminus/degaudit/internal/model"

func MapTransfer(source string, auditYear int, equivs []model.TransferEquiv) string {
    for _, e := range equivs {
        if e.SourceCode != source {
            continue
        }
        if auditYear < e.ValidFromYear || auditYear > e.ValidToYear {
            continue
        }
        return e.TargetCode
    }
    return source
}
