#!/usr/bin/env bash
set -euo pipefail

cd /app


patch -p1 <<'EOF'
--- a/src/matchcfg.c
+++ b/src/matchcfg.c
@@ -18,9 +18,15 @@
 	char *arg, *oattrib, *attrib, *cp = *condition, *target;
 	const char *ruser;
 	int r, result = 1, attributes = 0, negate;
+	struct expand_key keys[2] = { { 'h', host }, { '\0', NULL } };
 
 	ruser = options->user == NULL ? hop_pw->pw_name : options->user;
-	target = xstrdup(final_pass ? options->hostname : host);
+	if (final_pass)
+		target = xstrdup(options->hostname);
+	else if (options->hostname != NULL)
+		target = percent_expand(options->hostname, keys);
+	else
+		target = xstrdup(host);
 
 	while ((oattrib = attrib = strdelim(&cp)) && *attrib != '\0') {
 		if (*attrib == '#') {
EOF

patch -p1 <<'EOF'
--- a/src/main.c
+++ b/src/main.c
@@ -170,8 +170,7 @@
 	if (want_final_pass) {
 		free(options.hostname);
 		options.hostname = xstrdup(host);
-		process_config_files(options.host_arg, options.host_arg, 1,
-		    NULL);
+		process_config_files(host, options.host_arg, 1, NULL);
 	}
 
 	fill_default_options(&options);
@@ -199,7 +198,7 @@
 	snprintf(uidstr, sizeof(uidstr), "%llu",
 	    (unsigned long long)hop_pw->pw_uid);
 	keyalias = options.host_key_alias ?
-	    options.host_key_alias : host;
+	    options.host_key_alias : options.host_arg;
 	i = 0;
 	keys[i++] = (struct expand_key){ 'i', uidstr };
 	keys[i++] = (struct expand_key){ 'k', keyalias };
EOF

patch -p1 <<'EOF'
--- a/src/convtime.c
+++ b/src/convtime.c
@@ -65,7 +65,7 @@
 		secs *= multiplier;
 		if (total > INT_MAX - secs)
 			return -1;
-		total = secs;
+		total += secs;
 		p = endp;
 	}
 	return (int)total;
EOF

patch -p1 <<'EOF'
--- a/src/strlist.c
+++ b/src/strlist.c
@@ -28,7 +28,7 @@
 	int i, j;
 
 	for (i = j = 0; i < l->n; i++) {
-		if (match_pattern(pattern, l->v[i])) {
+		if (match_pattern(l->v[i], pattern)) {
 			free(l->v[i]);
 			continue;
 		}
EOF

patch -p1 <<'EOF'
--- a/src/jump.c
+++ b/src/jump.c
@@ -42,7 +42,7 @@
 		*cp = '\0';
 	rtrim(orig);
 
-	active &= o->jump_host == NULL;
+	active &= o->proxy_command == NULL && o->jump_host == NULL;
 	sdup = xstrdup(orig);
 	do {
 		if ((cp = strrchr(sdup, ',')) == NULL)
EOF

patch -p1 <<'EOF'
--- a/src/options.c
+++ b/src/options.c
@@ -76,7 +76,7 @@
 	if (o->identities_only == -1)
 		o->identities_only = 0;
 	if (o->server_alive_interval == -1)
-		o->server_alive_interval = 0;
+		o->server_alive_interval = o->batch_mode == 1 ? 300 : 0;
 	if (o->server_alive_count_max == -1)
 		o->server_alive_count_max = 3;
 	if (o->control_master == -1)
EOF

patch -p1 <<'EOF'
--- a/src/dump.c
+++ b/src/dump.c
@@ -56,7 +56,7 @@
 fmt_loglevel(int v)
 {
 	static const char *names[] = {
-		"QUIET", "FATAL", "ERROR", "INFO", "VERBOSE",
+		"SILENT", "FATAL", "ERROR", "INFO", "VERBOSE",
 		"DEBUG", "DEBUG2", "DEBUG3"
 	};
 
EOF

make clean
make
make check
