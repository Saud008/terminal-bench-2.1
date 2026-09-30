#include "hopcfg.h"

#include <ctype.h>
#include <netdb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>

/*
 * Split off the next host field of "host:port" or "[v6addr]:port", storing
 * the delimiter (':' or '/') in *delim.
 */
char *
hpdelim2(char **cp, char *delim)
{
	char *s, *old;

	if (cp == NULL || *cp == NULL)
		return NULL;

	old = s = *cp;
	if (*s == '[') {
		if ((s = strchr(s, ']')) == NULL)
			return NULL;
		s++;
	} else if ((s = strpbrk(s, ":/")) == NULL)
		s = *cp + strlen(*cp);

	switch (*s) {
	case '\0':
		*cp = NULL;
		break;
	case ':':
	case '/':
		if (delim != NULL)
			*delim = *s;
		*s = '\0';
		*cp = s + 1;
		break;
	default:
		return NULL;
	}
	return old;
}

char *
hpdelim(char **cp)
{
	char *r, delim = '\0';

	r = hpdelim2(cp, &delim);
	if (delim == '/')
		return NULL;
	return r;
}

char *
cleanhostname(char *host)
{
	size_t len = strlen(host);

	if (*host == '[' && len > 0 && host[len - 1] == ']') {
		host[len - 1] = '\0';
		return host + 1;
	}
	return host;
}

/* Parse [user@]host[:port]; returns 0 on success. */
int
parse_user_host_port(const char *s, char **userp, char **hostp, int *portp)
{
	char *sdup, *cp, *tmp;
	char *user = NULL, *host = NULL;
	int port = -1, ret = -1;

	if (userp != NULL)
		*userp = NULL;
	if (hostp != NULL)
		*hostp = NULL;
	if (portp != NULL)
		*portp = -1;

	sdup = tmp = xstrdup(s);
	if ((cp = strrchr(tmp, '@')) != NULL) {
		*cp = '\0';
		if (*tmp == '\0')
			goto out;
		user = xstrdup(tmp);
		tmp = cp + 1;
	}
	if ((cp = hpdelim(&tmp)) == NULL || *cp == '\0')
		goto out;
	host = xstrdup(cleanhostname(cp));
	if (tmp != NULL && *tmp != '\0') {
		if ((port = a2port(tmp)) <= 0)
			goto out;
	}
	if (userp != NULL) {
		*userp = user;
		user = NULL;
	}
	if (hostp != NULL) {
		*hostp = host;
		host = NULL;
	}
	if (portp != NULL)
		*portp = port;
	ret = 0;
 out:
	free(sdup);
	free(user);
	free(host);
	return ret;
}

static int
hexval(char c)
{
	if (c >= '0' && c <= '9')
		return c - '0';
	if (c >= 'a' && c <= 'f')
		return c - 'a' + 10;
	if (c >= 'A' && c <= 'F')
		return c - 'A' + 10;
	return -1;
}

static char *
urldecode(const char *src)
{
	char *ret, *dst;
	int hi, lo;

	ret = dst = xmalloc(strlen(src) + 1);
	for (; *src != '\0'; src++) {
		switch (*src) {
		case '+':
			*dst++ = ' ';
			break;
		case '%':
			if ((hi = hexval(src[1])) < 0 ||
			    (lo = hexval(src[2])) < 0 || (hi << 4 | lo) == 0) {
				free(ret);
				return NULL;
			}
			*dst++ = (char)(hi << 4 | lo);
			src += 2;
			break;
		default:
			*dst++ = *src;
			break;
		}
	}
	*dst = '\0';
	return ret;
}

/*
 * Parse ssh://[user@]host[:port] (no path allowed).  Returns 0 on success,
 * 1 if the string is not an ssh URI and -1 if it is a malformed one.
 */
int
parse_ssh_uri(const char *uri, char **userp, char **hostp, int *portp)
{
	char *uridup, *cp, *tmp, ch = '\0';
	char *user = NULL, *host = NULL;
	int port = -1, ret = -1;

	if (strncmp(uri, "ssh://", 6) != 0)
		return 1;
	uri += 6;

	if (userp != NULL)
		*userp = NULL;
	if (hostp != NULL)
		*hostp = NULL;
	if (portp != NULL)
		*portp = -1;

	uridup = tmp = xstrdup(uri);
	if ((cp = strchr(tmp, '@')) != NULL) {
		char *delim;

		*cp = '\0';
		if ((delim = strchr(tmp, ';')) != NULL)
			*delim = '\0';
		if (*tmp == '\0')
			goto out;
		if ((user = urldecode(tmp)) == NULL)
			goto out;
		tmp = cp + 1;
	}
	if ((cp = hpdelim2(&tmp, &ch)) == NULL || *cp == '\0')
		goto out;
	host = xstrdup(cleanhostname(cp));
	if (!valid_domain(host, 0))
		goto out;
	if (tmp != NULL && *tmp != '\0') {
		if (ch == ':') {
			if ((cp = strchr(tmp, '/')) != NULL)
				*cp = '\0';
			if ((port = a2port(tmp)) <= 0)
				goto out;
			tmp = cp ? cp + 1 : NULL;
		}
		if (tmp != NULL && *tmp != '\0')
			goto out;
	}
	if (userp != NULL) {
		*userp = user;
		user = NULL;
	}
	if (hostp != NULL) {
		*hostp = host;
		host = NULL;
	}
	if (portp != NULL)
		*portp = port;
	ret = 0;
 out:
	free(uridup);
	free(user);
	free(host);
	return ret;
}

int
valid_domain(char *name, int makelower)
{
	size_t i, l = strlen(name);
	unsigned char c, last = '\0';

	if (l == 0)
		return 0;
	if (!isalpha((unsigned char)name[0]) && !isdigit((unsigned char)name[0]))
		return 0;
	for (i = 0; i < l; i++) {
		c = tolower((unsigned char)name[i]);
		if (makelower)
			name[i] = (char)c;
		if (last == '.' && c == '.')
			return 0;
		if (c != '.' && c != '-' && !isalnum(c) && c != '_')
			return 0;
		last = c;
	}
	if (name[l - 1] == '.')
		name[l - 1] = '\0';
	return 1;
}

int
valid_hostname(const char *s)
{
	size_t i;

	if (*s == '-')
		return 0;
	for (i = 0; s[i] != '\0'; i++) {
		if (strchr("'`\"$\\;&<>|(){},", s[i]) != NULL ||
		    isspace((unsigned char)s[i]) || iscntrl((unsigned char)s[i]))
			return 0;
	}
	return 1;
}

int
valid_ruser(const char *s)
{
	size_t i;

	if (*s == '-')
		return 0;
	for (i = 0; s[i] != '\0'; i++) {
		if (iscntrl((unsigned char)s[i]))
			return 0;
		if (strchr("'`\";&<>|(){}", s[i]) != NULL)
			return 0;
		if (isspace((unsigned char)s[i]) && s[i + 1] == '-')
			return 0;
		if (s[i] == '\\' && s[i + 1] == '\0')
			return 0;
	}
	return 1;
}

static int
is_addr_fast(const char *name)
{
	return strchr(name, '%') != NULL || strchr(name, ':') != NULL ||
	    strspn(name, "0123456789.") == strlen(name);
}

/*
 * Stores the canonical numeric form of name in out if name parses as a
 * single numeric address.  Returns 1 on success.
 */
int
canonical_addr(const char *name, char *out, size_t outlen)
{
	struct addrinfo hints, *res;
	char port[8];

	snprintf(port, sizeof(port), "%d", DEFAULT_SSH_PORT);
	memset(&hints, 0, sizeof(hints));
	hints.ai_family = AF_UNSPEC;
	hints.ai_socktype = SOCK_STREAM;
	hints.ai_flags = AI_NUMERICHOST | AI_NUMERICSERV;
	if (getaddrinfo(name, port, &hints, &res) != 0)
		return 0;
	if (res == NULL || res->ai_next != NULL) {
		if (res != NULL)
			freeaddrinfo(res);
		return 0;
	}
	if (getnameinfo(res->ai_addr, res->ai_addrlen, out, outlen, NULL, 0,
	    NI_NUMERICHOST) != 0) {
		freeaddrinfo(res);
		return 0;
	}
	freeaddrinfo(res);
	return 1;
}

/* Returns 1 if name looks like, or parses as, a numeric address. */
int
is_addr(const char *name)
{
	char buf[NI_MAXHOST];

	return is_addr_fast(name) || canonical_addr(name, buf, sizeof(buf));
}
