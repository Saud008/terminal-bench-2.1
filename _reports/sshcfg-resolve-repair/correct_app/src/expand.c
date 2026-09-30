#include "hopcfg.h"

#include <ctype.h>
#include <pwd.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

struct buf {
	char *s;
	size_t len, cap;
};

static void
buf_put(struct buf *b, const char *s, size_t n)
{
	if (b->len + n + 1 > b->cap) {
		b->cap = (b->len + n + 1) * 2;
		b->s = xreallocarray(b->s, b->cap, 1);
	}
	memcpy(b->s + b->len, s, n);
	b->len += n;
	b->s[b->len] = '\0';
}

/*
 * Expand %-tokens (when keys != NULL) and ${VAR} references (when dollar is
 * set).  Sets *err and returns NULL on a malformed string, an unknown token
 * or an unset environment variable.
 */
static char *
expand(int *err, int dollar, const char *string, const struct expand_key *keys)
{
	struct buf b = { NULL, 0, 0 };
	const char *varend, *val;
	char *var;
	size_t len;
	int i, missing = 0;

	*err = 1;
	buf_put(&b, "", 0);
	for (; *string != '\0'; string++) {
		if (dollar && string[0] == '$' && string[1] == '{') {
			string += 2;
			if ((varend = strchr(string, '}')) == NULL) {
				error("environment variable '%s' missing "
				    "closing '}'", string);
				goto out;
			}
			len = varend - string;
			if (len == 0) {
				error("zero-length environment variable");
				goto out;
			}
			var = xstrndup(string, len);
			if ((val = getenv(var)) == NULL) {
				error("env var ${%s} has no value", var);
				missing = 1;
			} else
				buf_put(&b, val, strlen(val));
			free(var);
			string += len;
			continue;
		}
		if (*string != '%' || keys == NULL) {
			buf_put(&b, string, 1);
			continue;
		}
		string++;
		if (*string == '%') {
			buf_put(&b, "%", 1);
			continue;
		}
		if (*string == '\0') {
			error("invalid format");
			goto out;
		}
		for (i = 0; keys[i].key != '\0'; i++) {
			if (keys[i].key == *string) {
				buf_put(&b, keys[i].value, strlen(keys[i].value));
				break;
			}
		}
		if (keys[i].key == '\0') {
			error("unknown key %%%c", *string);
			goto out;
		}
	}
	if (!missing)
		*err = 0;
 out:
	if (*err) {
		free(b.s);
		return NULL;
	}
	return b.s;
}

char *
percent_expand(const char *string, const struct expand_key *keys)
{
	char *ret;
	int err;

	if ((ret = expand(&err, 0, string, keys)) == NULL || err)
		fatal("percent_expand: failed");
	return ret;
}

char *
percent_dollar_expand(const char *string, const struct expand_key *keys)
{
	char *ret;
	int err;

	if ((ret = expand(&err, 1, string, keys)) == NULL || err)
		fatal("invalid environment variable expansion");
	return ret;
}

char *
dollar_expand(int *err, const char *string)
{
	return expand(err, 1, string, NULL);
}

/* Expand a leading "~" or "~user" using the password database. */
char *
tilde_expand_filename(const char *filename)
{
	char *copy, *ocopy, *ret;
	const char *path = NULL, *user = NULL;
	struct passwd *pw;
	size_t len;
	int slash;

	if (*filename != '~')
		return xstrdup(filename);
	ocopy = copy = xstrdup(filename + 1);

	if (*copy == '\0')
		path = NULL;
	else if (*copy == '/') {
		copy += strspn(copy, "/");
		path = *copy == '\0' ? NULL : copy;
	} else {
		user = copy;
		if ((path = strchr(copy, '/')) != NULL) {
			copy[path - copy] = '\0';
			path++;
			path += strspn(path, "/");
			if (*path == '\0')
				path = NULL;
		}
	}
	if (user != NULL) {
		if ((pw = getpwnam(user)) == NULL)
			fatal("tilde_expand: No such user %s", user);
	} else if ((pw = getpwuid(getuid())) == NULL)
		fatal("tilde_expand: No such uid %ld", (long)getuid());

	slash = (len = strlen(pw->pw_dir)) == 0 || pw->pw_dir[len - 1] != '/';
	xasprintf(&ret, "%s%s%s", pw->pw_dir, slash ? "/" : "",
	    path != NULL ? path : "");
	free(ocopy);
	return ret;
}

int
valid_env_name(const char *name)
{
	const char *cp;

	if (name[0] == '\0')
		return 0;
	for (cp = name; *cp != '\0'; cp++) {
		if (!isalnum((unsigned char)*cp) && *cp != '_')
			return 0;
	}
	return 1;
}
