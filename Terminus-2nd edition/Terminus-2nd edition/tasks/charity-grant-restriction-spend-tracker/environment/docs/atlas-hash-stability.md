# atlas hash stability

atlas_digest is sha256 over compact JSON of grant_balances, rejections, and amendment_pass keys in that object shape. Field order in the digest input follows Go json.Marshal struct field order. Because the digest body includes `rejections`, an empty rejection list must be encoded as `[]` (not `null`); a null value changes the digest bytes and fails atlas equality checks.
