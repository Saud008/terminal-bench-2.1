#!/usr/bin/env bash
set -euo pipefail

cd /app

patch -p1 <<'EOF'
--- a/src/readconf.c
+++ b/src/readconf.c
@@ -89,7 +89,6 @@
     int linenum, int *activep, int flags, int *want_final_pass, int depth)
 {
 	char *str, **charptr, *keyword, *arg, *arg2;
-	const char *cp;
 	char **oav = NULL, **av, fwdarg[256];
 	int oac = 0, ac, value, value2, *intptr, cmdline = 0, oactive, negated;
 	int remotefwd, dynamicfwd, i, r, ret = -1;
@@ -464,13 +463,14 @@
 		break;
 
 	case oSetEnv:
+		value = options->setenv.n;
 		while ((arg = argv_next(&ac, &av)) != NULL) {
 			if (strchr(arg, '=') == NULL) {
 				error("%s line %d: Invalid SetEnv.",
 				    filename, linenum);
 				goto out;
 			}
-			if (!*activep)
+			if (!*activep || value != 0)
 				continue;
 			len = strchr(arg, '=') - arg;
 			for (i = 0; i < options->setenv.n; i++) {
@@ -531,8 +531,14 @@
 			negated = *arg == '!';
 			if (negated)
 				arg++;
-			if (match_pattern(host, arg))
-				*activep = !negated;
+			if (match_pattern(host, arg)) {
+				if (negated) {
+					*activep = 0;
+					argv_consume(&ac);
+					break;
+				}
+				*activep = 1;
+			}
 		}
 		break;
 
@@ -572,14 +578,10 @@
 				    filename, linenum, arg);
 				goto out;
 			}
-			if (*arg != '/' && *arg != '~') {
-				/* relative to the including file */
-				if ((cp = strrchr(filename, '/')) != NULL)
-					xasprintf(&arg2, "%.*s/%s",
-					    (int)(cp - filename), filename, arg);
-				else
-					arg2 = xstrdup(arg);
-			} else
+			if (*arg != '/' && *arg != '~')
+				xasprintf(&arg2, "%s/%s", (flags & CONF_USER) ?
+				    "~/.ssh" : "/etc/ssh", arg);
+			else
 				arg2 = xstrdup(arg);
 			memset(&gl, 0, sizeof(gl));
 			r = glob(arg2, GLOB_TILDE, NULL, &gl);
@@ -606,10 +608,10 @@
 					globfree(&gl);
 					goto out;
 				}
+				*activep = oactive;
 				if (r != 1)
 					value = -1;
 			}
-			*activep = oactive;
 			globfree(&gl);
 		}
 		if (value != 0)
EOF

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
