#include "hopcfg.h"

#include <stdlib.h>
#include <string.h>

void
strlist_append(struct strlist *l, const char *s)
{
	l->v = xreallocarray(l->v, l->n + 1, sizeof(*l->v));
	l->v[l->n++] = xstrdup(s);
}

int
strlist_contains(const struct strlist *l, const char *s)
{
	int i;

	for (i = 0; i < l->n; i++)
		if (strcmp(l->v[i], s) == 0)
			return 1;
	return 0;
}

/* Drop every entry that the wildcard pattern matches, keeping order. */
void
strlist_remove_matching(struct strlist *l, const char *pattern)
{
	int i, j;

	for (i = j = 0; i < l->n; i++) {
		if (match_pattern(l->v[i], pattern)) {
			free(l->v[i]);
			continue;
		}
		l->v[j++] = l->v[i];
	}
	l->n = j;
}

void
strlist_clear(struct strlist *l)
{
	int i;

	for (i = 0; i < l->n; i++)
		free(l->v[i]);
	free(l->v);
	l->v = NULL;
	l->n = 0;
}
