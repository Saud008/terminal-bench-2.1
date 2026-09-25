package substgate

import "github.com/terminus/degaudit/internal/model"

func ActiveSubstitutions(auditTerm string, subs []model.Substitution) map[string]string {
    out := map[string]string{}
    for _, s := range subs {
        if auditTerm <= s.ExpiresAfterTerm {
            out[s.ReplacesReqID] = s.SubReqID
        }
    }
    return out
}
