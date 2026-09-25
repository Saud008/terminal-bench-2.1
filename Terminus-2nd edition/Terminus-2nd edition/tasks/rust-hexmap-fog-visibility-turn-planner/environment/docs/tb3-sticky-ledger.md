# Fog reveal mask

`/app/work/fog-mask/<run-id>.json` holds the sticky fog mask for a playtest run.

A cell becomes visible when **any** placed unit has that cell within its vision radius and clear LOS.

Sticky fog: once a cell is visible in the mask for a run, later `reveal-fog` calls keep it visible even if units move or leave, until `/app/scripts/reset-playfield.sh` clears run state. Each `reveal-fog` unions newly visible cells into the existing mask.
