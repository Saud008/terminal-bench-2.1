package issaud

import "strings"

// AudienceOK enforces issuer-audience-contract.md audience binding.
func AudienceOK(tokenAud, policyAud []string) bool {
    if len(policyAud) == 0 {
        return true
    }
    for _, ta := range tokenAud {
        for _, pa := range policyAud {
            if strings.TrimSpace(ta) == strings.TrimSpace(pa) {
                return true
            }
        }
    }
    return false
}

func IssuerOK(tokenIss, policyIss string) bool {
    return strings.TrimSpace(strings.ToLower(tokenIss)) == strings.TrimSpace(strings.ToLower(policyIss))
}
