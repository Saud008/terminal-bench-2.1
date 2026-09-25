# Engineering problem contract

whres explains Python wheel resolution for offline package indexes using Rust. The agent implements load, analyze, and emit stages that cross PEP 440 version math, environment marker evaluation, wheel tag compatibility, yanked release policy, and deterministic candidate reporting.

Verifier cases generate random package names, versions, tags, and markers. Correct behavior requires reading /app/docs/ contracts and patching multiple Rust modules so analyze output and emit reports match independent pytest reference math.
