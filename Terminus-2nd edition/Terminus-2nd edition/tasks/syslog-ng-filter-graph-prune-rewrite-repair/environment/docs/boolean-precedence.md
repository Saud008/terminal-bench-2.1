# Boolean filter precedence

Expressions may combine facility(), level(), and program() atoms with && and ||.

Parentheses define explicit grouping. Without parentheses, AND (&&) binds tighter than OR (||).

Example: facility(auth) && level(warn) || facility(mail) means (facility(auth) && level(warn)) || facility(mail).

Evaluation is short-circuit left-to-right within each precedence level.
