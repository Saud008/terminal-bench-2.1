# Fixture catalog

Bundled waveform assay fixtures for calibration closure verification. See `/app/docs/scientific-computing-workflow.md`.

Bundled SLWS snippets live under /app/fixtures/slws/. catalog.json lists stems and absolute paths.

| Stem | Notes |
|------|-------|
| calm-pwave | Baseline P and S picks |
| leap-edge | leap_marker with epoch adjacent to configured leap epoch |
| clip-heavy | Dense clipped mask inside P window |
| polarity-flip | DEF2 station with sheet inversion |
| shuffle-picks | Picks out of file order; digest uses sorted order |
| decode-invariant-fail | Duplicate pick indices — decode rejects |
| bad-crc | Invalid checksum |

Hidden verifier fixtures may appear under /opt/verifier-fixtures/slws/ with alternate leap tables and polarity sheets documented in leap-calendar.md and phase-window-contract.md.
