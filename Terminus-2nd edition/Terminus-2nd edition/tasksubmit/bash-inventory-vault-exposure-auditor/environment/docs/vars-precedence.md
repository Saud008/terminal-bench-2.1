# Variable precedence

For each host, build ordered group list starting with all, then parent groups, then direct groups. More specific child group vars override parent group vars.

Load group_vars files in group order from least specific to most specific. host_vars override all group_vars.

Secret keys matching password, secret, api_key, token, or private_key suffix patterns require vault markers when values are sensitive.
