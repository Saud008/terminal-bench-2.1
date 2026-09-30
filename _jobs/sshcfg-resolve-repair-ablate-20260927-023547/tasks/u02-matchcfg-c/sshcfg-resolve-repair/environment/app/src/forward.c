#include "hopcfg.h"

#include <ctype.h>
#include <netdb.h>
#include <stdlib.h>
#include <string.h>
#include <sys/un.h>

#define PATH_MAX_SUN (sizeof(((struct sockaddr_un *)0)->sun_path))

struct fwdarg {
	char *arg;
	int ispath;
};

/*
 * Parse the next ':'-separated field of a forwarding spec.  A field in
 * square brackets is taken literally; any field containing '/' is a path.
 */
static int
parse_fwd_field(char **p, struct fwdarg *fwd)
{
	char *ep, *cp = *p;
	int ispath = 0;

	if (*cp == '\0') {
		*p = NULL;
		return -1;
	}

	if (*cp == '[') {
		for (ep = cp + 1; *ep != ']' && *ep != '\0'; ep++) {
			if (*ep == '/')
				ispath = 1;
		}
		if (ep[0] != ']' || (ep[1] != ':' && ep[1] != '\0'))
			return -1;
		*ep++ = '\0';
		if (*ep != '\0')
			*ep++ = '\0';
		fwd->arg = cp + 1;
		fwd->ispath = ispath;
		*p = ep;
		return 0;
	}

	for (cp = *p; *cp != '\0'; cp++) {
		switch (*cp) {
		case '\\':
			memmove(cp, cp + 1, strlen(cp + 1) + 1);
			if (*cp == '\0')
				return -1;
			break;
		case '/':
			ispath = 1;
			break;
		case ':':
			*cp++ = '\0';
			goto done;
		}
	}
 done:
	fwd->arg = *p;
	fwd->ispath = ispath;
	*p = cp;
	return 0;
}

void
free_forward(struct forward *fwd)
{
	free(fwd->listen_host);
	free(fwd->listen_path);
	free(fwd->connect_host);
	free(fwd->connect_path);
	memset(fwd, 0, sizeof(*fwd));
}

/*
 * Parse a forwarding specification:
 *   [listen_host:]listen_port|listen_path:connect_host:connect_port|path
 * or, for dynamic forwards, [listen_host:]listen_port.
 * Returns the number of fields parsed, or 0 on error.
 */
int
parse_forward(struct forward *fwd, const char *spec, int dynamicfwd,
    int remotefwd)
{
	struct fwdarg a[4];
	char *p, *cp;
	int i, err;

	memset(fwd, 0, sizeof(*fwd));
	memset(a, 0, sizeof(a));

	cp = p = dollar_expand(&err, spec);
	if (p == NULL || err)
		return 0;

	while (isspace((unsigned char)*cp))
		cp++;

	for (i = 0; i < 4; ++i) {
		if (parse_fwd_field(&cp, &a[i]) != 0)
			break;
	}
	if (cp != NULL && *cp != '\0')
		i = 0;

	switch (i) {
	case 1:
		if (a[0].ispath) {
			fwd->listen_path = xstrdup(a[0].arg);
			fwd->listen_port = PORT_STREAMLOCAL;
		} else {
			fwd->listen_host = NULL;
			fwd->listen_port = a2port(a[0].arg);
		}
		fwd->connect_host = xstrdup("socks");
		break;
	case 2:
		if (a[0].ispath && a[1].ispath) {
			fwd->listen_path = xstrdup(a[0].arg);
			fwd->listen_port = PORT_STREAMLOCAL;
			fwd->connect_path = xstrdup(a[1].arg);
			fwd->connect_port = PORT_STREAMLOCAL;
		} else if (a[1].ispath) {
			fwd->listen_host = NULL;
			fwd->listen_port = a2port(a[0].arg);
			fwd->connect_path = xstrdup(a[1].arg);
			fwd->connect_port = PORT_STREAMLOCAL;
		} else {
			fwd->listen_host = xstrdup(a[0].arg);
			fwd->listen_port = a2port(a[1].arg);
			fwd->connect_host = xstrdup("socks");
		}
		break;
	case 3:
		if (a[0].ispath) {
			fwd->listen_path = xstrdup(a[0].arg);
			fwd->listen_port = PORT_STREAMLOCAL;
			fwd->connect_host = xstrdup(a[1].arg);
			fwd->connect_port = a2port(a[2].arg);
		} else if (a[2].ispath) {
			fwd->listen_host = xstrdup(a[0].arg);
			fwd->listen_port = a2port(a[1].arg);
			fwd->connect_path = xstrdup(a[2].arg);
			fwd->connect_port = PORT_STREAMLOCAL;
		} else {
			fwd->listen_host = NULL;
			fwd->listen_port = a2port(a[0].arg);
			fwd->connect_host = xstrdup(a[1].arg);
			fwd->connect_port = a2port(a[2].arg);
		}
		break;
	case 4:
		fwd->listen_host = xstrdup(a[0].arg);
		fwd->listen_port = a2port(a[1].arg);
		fwd->connect_host = xstrdup(a[2].arg);
		fwd->connect_port = a2port(a[3].arg);
		break;
	default:
		i = 0;
	}
	free(p);

	if (dynamicfwd) {
		if (!(i == 1 || i == 2))
			goto fail;
	} else {
		if (!(i == 3 || i == 4)) {
			if (fwd->connect_path == NULL &&
			    fwd->listen_path == NULL)
				goto fail;
		}
		if (fwd->connect_port <= 0 && fwd->connect_path == NULL)
			goto fail;
	}
	if ((fwd->listen_port < 0 && fwd->listen_path == NULL) ||
	    (!remotefwd && fwd->listen_port == 0))
		goto fail;
	if (fwd->connect_host != NULL && strlen(fwd->connect_host) >= NI_MAXHOST)
		goto fail;
	if (fwd->connect_path != NULL && strlen(fwd->connect_path) >= PATH_MAX_SUN)
		goto fail;
	if (fwd->listen_host != NULL && strlen(fwd->listen_host) >= NI_MAXHOST)
		goto fail;
	if (fwd->listen_path != NULL && strlen(fwd->listen_path) >= PATH_MAX_SUN)
		goto fail;
	return i;

 fail:
	free_forward(fwd);
	return 0;
}

static int
same_str(const char *a, const char *b)
{
	if (a == NULL || b == NULL)
		return a == b;
	return strcmp(a, b) == 0;
}

static int
forward_equals(const struct forward *a, const struct forward *b)
{
	return same_str(a->listen_host, b->listen_host) &&
	    a->listen_port == b->listen_port &&
	    same_str(a->listen_path, b->listen_path) &&
	    same_str(a->connect_host, b->connect_host) &&
	    a->connect_port == b->connect_port &&
	    same_str(a->connect_path, b->connect_path);
}

/* Takes ownership of the strings in fwd; duplicates are dropped. */
void
add_forward(struct fwdlist *l, const struct forward *fwd)
{
	int i;

	for (i = 0; i < l->n; i++) {
		if (forward_equals(fwd, &l->v[i])) {
			struct forward tmp = *fwd;

			free_forward(&tmp);
			return;
		}
	}
	l->v = xreallocarray(l->v, l->n + 1, sizeof(*l->v));
	l->v[l->n++] = *fwd;
}

void
clear_forwards(struct fwdlist *l)
{
	int i;

	for (i = 0; i < l->n; i++)
		free_forward(&l->v[i]);
	free(l->v);
	l->v = NULL;
	l->n = 0;
}
