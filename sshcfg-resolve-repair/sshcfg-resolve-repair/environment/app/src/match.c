#include "hopcfg.h"

#include <ctype.h>
#include <stdlib.h>
#include <string.h>

/* Case-sensitive match of s against a pattern using '*' and '?'. */
int
match_pattern(const char *s, const char *pattern)
{
	for (;;) {
		if (!*pattern)
			return !*s;

		if (*pattern == '*') {
			while (*pattern == '*')
				pattern++;
			if (!*pattern)
				return 1;
			if (*pattern != '?' && *pattern != '*') {
				for (; *s; s++)
					if (*s == *pattern &&
					    match_pattern(s + 1, pattern + 1))
						return 1;
				return 0;
			}
			for (; *s; s++)
				if (match_pattern(s, pattern))
					return 1;
			return 0;
		}
		if (!*s)
			return 0;
		if (*pattern != '?' && *pattern != *s)
			return 0;
		s++;
		pattern++;
	}
}

/*
 * Match string against a comma-separated list of patterns, each of which
 * may be negated with '!'.  Returns -1 when a negated pattern matches,
 * 1 on a positive match and 0 when nothing matched.
 */
int
match_pattern_list(const char *string, const char *pattern, int dolower)
{
	char sub[1024];
	int negated, got_positive = 0;
	size_t i, subi, len = strlen(pattern);

	for (i = 0; i < len;) {
		if (pattern[i] == '!') {
			negated = 1;
			i++;
		} else
			negated = 0;

		for (subi = 0; i < len && subi < sizeof(sub) - 1 &&
		    pattern[i] != ','; subi++, i++)
			sub[subi] = dolower && isupper((unsigned char)pattern[i]) ?
			    tolower((unsigned char)pattern[i]) : pattern[i];
		if (subi >= sizeof(sub) - 1)
			return 0;
		if (i < len && pattern[i] == ',')
			i++;
		sub[subi] = '\0';

		if (match_pattern(string, sub)) {
			if (negated)
				return -1;
			got_positive = 1;
		}
	}
	return got_positive;
}

int
match_hostname(const char *host, const char *pattern)
{
	char *copy = xstrdup(host);
	int r;

	lowercase(copy);
	r = match_pattern_list(copy, pattern, 1);
	free(copy);
	return r;
}
