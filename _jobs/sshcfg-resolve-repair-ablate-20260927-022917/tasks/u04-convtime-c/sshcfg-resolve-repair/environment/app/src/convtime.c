#include "hopcfg.h"

#include <errno.h>
#include <limits.h>
#include <netdb.h>
#include <netinet/in.h>
#include <stdlib.h>
#include <string.h>

#define MINUTES	60
#define HOURS	(MINUTES * 60)
#define DAYS	(HOURS * 24)
#define WEEKS	(DAYS * 7)

/*
 * Convert a time specification such as "90", "90s", "1h30m" or "2w" to
 * seconds.  Returns -1 if the string is not a valid time.
 */
int
convtime(const char *s)
{
	long total = 0, secs, multiplier;
	const char *p = s;
	char *endp;

	if (p == NULL || *p == '\0')
		return -1;

	while (*p) {
		errno = 0;
		secs = strtol(p, &endp, 10);
		if (p == endp || (errno == ERANGE &&
		    (secs == LONG_MIN || secs == LONG_MAX)) || secs < 0)
			return -1;

		multiplier = 1;
		switch (*endp++) {
		case '\0':
			endp--;
			break;
		case 's':
		case 'S':
			break;
		case 'm':
		case 'M':
			multiplier = MINUTES;
			break;
		case 'h':
		case 'H':
			multiplier = HOURS;
			break;
		case 'd':
		case 'D':
			multiplier = DAYS;
			break;
		case 'w':
		case 'W':
			multiplier = WEEKS;
			break;
		default:
			return -1;
		}
		if (secs > INT_MAX / multiplier)
			return -1;
		secs *= multiplier;
		if (total > INT_MAX - secs)
			return -1;
		total = secs;
		p = endp;
	}
	return (int)total;
}

static long long
strtonum_range(const char *s, long long lo, long long hi, const char **errstr)
{
	long long v;
	char *end;

	*errstr = NULL;
	if (s == NULL || *s == '\0') {
		*errstr = "invalid";
		return 0;
	}
	errno = 0;
	v = strtoll(s, &end, 10);
	if (*end != '\0' || end == s)
		*errstr = "invalid";
	else if ((v == LLONG_MIN && errno == ERANGE) || v < lo)
		*errstr = "too small";
	else if ((v == LLONG_MAX && errno == ERANGE) || v > hi)
		*errstr = "too large";
	return *errstr == NULL ? v : 0;
}

/* Port number or service name; -1 if invalid. */
int
a2port(const char *s)
{
	struct servent *se;
	const char *errstr;
	long long port;

	port = strtonum_range(s, 0, 65535, &errstr);
	if (errstr == NULL)
		return (int)port;
	if ((se = getservbyname(s, "tcp")) != NULL)
		return ntohs(se->s_port);
	return -1;
}

const char *
atoi_err(const char *s, int *val)
{
	const char *errstr;
	long long num;

	if (s == NULL || *s == '\0')
		return "missing";
	num = strtonum_range(s, 0, INT_MAX, &errstr);
	if (errstr == NULL)
		*val = (int)num;
	return errstr;
}
