package kidmap

import "github.com/terminus/oidcgov/internal/model"

// FindKey resolves JWKS keys per kid-lookup-contract.md.
func FindKey(kid string, keys []model.JWKSKey) (model.JWKSKey, bool) {
    for _, k := range keys {
        if k.KID == kid {
            return k, true
        }
    }
    return model.JWKSKey{}, false
}
