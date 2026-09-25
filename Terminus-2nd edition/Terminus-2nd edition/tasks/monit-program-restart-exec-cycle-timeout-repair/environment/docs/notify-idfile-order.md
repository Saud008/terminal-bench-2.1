# Notify and idfile order

Event handler mail or notify log lines must be written only after the monit id state file is updated for the same transition.

The export boolean notify_before_idfile is true when any notify log line for a transition appears before the idfile mtime marker for that transition.

Each timeline step that emits notify includes idfile_written then notify_emitted ordering when correct.
