# Playtest win condition

This planner supports tactics playtest fog simulation on a hex playfield. The win condition for a sealed atlas is meeting the board's `target_reveal` threshold: when sticky visible cell count is at least `target_reveal`, `win_condition_met` is true.

Designers use this tick/turn loop to tune vision classes, elevation blockers, and fog reveal pacing before shipping a level.
