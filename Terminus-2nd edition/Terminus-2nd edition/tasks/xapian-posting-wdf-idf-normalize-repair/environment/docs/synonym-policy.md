# Synonym expansion

Each document may include a synonyms object mapping a canonical term to an array of extra surface forms. During scoring, effective_wdf(q, d) = max(wdf(q, d), max_{s in expansions(q, d)} wdf(s, d)). Synonym surface forms never add their WDF on top of the canonical term; take the maximum only.
