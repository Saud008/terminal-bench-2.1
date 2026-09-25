# PAM service file grammar

Service files live under services/ in each scenario bundle. Blank lines and lines beginning with # are ignored.

Module lines contain four fields: type, control, module path, and optional arguments. Type is one of auth, account, password, session. Control is one of required, requisite, sufficient, optional.

Directives begin with @. Supported directives: @include relative-path and @include-substack relative-path. Relative paths resolve from the directory containing the file that references them.
