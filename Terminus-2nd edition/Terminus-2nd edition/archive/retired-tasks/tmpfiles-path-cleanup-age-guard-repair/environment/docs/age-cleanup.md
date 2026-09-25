# Age cleanup contract

For r! lines, a candidate path is eligible for removal at instant NOW when:

NOW minus max(atime, btime) is greater than or equal to the rule age in seconds.

Use both access and birth timestamps. mtime alone is not sufficient and must not be used for the age gate. When atime and btime differ, the later timestamp controls eligibility.

If the path is missing from the tree, skip silently.
