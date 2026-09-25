# Unit drop-in precedence

Parse the base NAME.timer file first. Then apply fragments from NAME.timer.d sorted by basename ascending. Later fragments override earlier keys in the Timer section.

Record applied fragment basenames in drop_in_overrides_applied sorted lexicographically.
