# Issuer and audience binding

Issuer comparison is case-insensitive trimmed string equality.

When policy.audiences is non-empty, every token aud value must match some policy audience entry. Partial audience match is rejection. Example token audiences include api.example.net and admin.example.net; a policy listing only api.example.net rejects tokens that also list admin.example.net.
