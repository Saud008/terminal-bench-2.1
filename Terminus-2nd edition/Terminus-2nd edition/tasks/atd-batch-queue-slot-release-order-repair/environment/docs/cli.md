# CLI

at-replay replay --scenario NAME --seed SEED --export PATH runs one scheduling pass. Optional --clock EPOCH_SEC sets the replay instant. TB3_CLOCK_EPOCH overrides --clock when set.

Verifier harness (not part of the agent image): tests/test.sh stages golden reference modules under a temp directory and sets VERIFIER_GOLDEN_LIB for partial-fix probe tests only.
