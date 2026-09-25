# Matrix expansion contract

Expand parallel matrix rows into job instance names by sorting matrix keys lexicographically before building the suffix path segments. Format: base/key1=val1/key2=val2. Two matrix rows that canonicalize to the same name mark duplicate expansion true on the later row. Hidden pipelines under runtime overlay directories follow the same contract.
