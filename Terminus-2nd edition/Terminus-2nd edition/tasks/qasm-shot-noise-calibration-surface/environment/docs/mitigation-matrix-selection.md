# Mitigation matrix selection

After normalization, qasmenv selects one mitigation matrix from the candidates array in staging.

Filter candidates to those whose dimension equals the number of distinct qubits in the histogram. Ignore candidates with mismatched dimension.

Among remaining candidates, choose the highest priority integer. Larger priority wins.

When two or more candidates share the highest priority, apply seed manifest tie-break: let prefix be the first six characters of seed_hash from the staged manifest. Select the candidate whose id is lexicographically smallest among those with id greater than or equal to prefix. If no candidate id satisfies id >= prefix, select the lexicographically smallest id among the tied candidates.

The selected matrix id is recorded in the envelope ledger as selected_matrix_id.

Hidden verifier runs may supply TB3_SEED_OFFSET as an integer appended to the tie-break prefix as prefix:offset before comparison.
