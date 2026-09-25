# Default inheritance

Default rights come from defaults.json by objectClass on the entry. Defaults apply only when no explicit ACE matched the probe right and attribute after ACE trust ranking (`deny-before-allow.md`). Export must evaluate explicit ACE rows before inherited objectClass defaults.

An ACE block with INHERIT no on an entry blocks default inheritance for that entry only; explicit ACEs on the entry still apply.

Inherited defaults never override an explicit deny ACE.
