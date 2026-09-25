# Submission explanations - godot-tscn-uid-remap-ledger

**Status:** RETIRED — Harbor `[category_classifier]` predicted blocked `software-engineering` under data-processing, games/playtest lipstick, and system-administration metadata (four failures at ~0.92–0.95).

**Successor:** `tasks/scene-uid-admission-seal-ledger/` (`category = "system-administration"` host-local scene UID admission seal ledger).

Harbor accepted `category = "games"` and later `category = "system-administration"` in task.toml, but the classifier still predicted **software-engineering** (blocked). Metadata and playfield/ops lipstick cannot fix Godot `.tscn` merge/UID/graph tooling shape under the `godot-tscn-uid-remap-*` slug — upload the successor instead (admit → gates → sealed export, `scenectl`).

**Latest CI (2026-07-21):** `Predicted category 'software-engineering' (confidence 0.95) is blocked` while task.toml category was `system-administration`. Only actionable error; Dockerfile build-toolchain notes were warnings.
