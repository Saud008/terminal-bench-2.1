# rule-step-sequence.md

Rule steps execute in file order: take selects the root bucket, chooseleaf selects osd leaves per host, emit records the acting set. Do not reorder emit before chooseleaf.
