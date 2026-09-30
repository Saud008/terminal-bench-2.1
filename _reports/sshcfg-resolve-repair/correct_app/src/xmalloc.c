#include "hopcfg.h"

#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void *
xmalloc(size_t size)
{
	void *p;

	if (size == 0)
		size = 1;
	if ((p = malloc(size)) == NULL)
		fatal("out of memory allocating %zu bytes", size);
	return p;
}

void *
xcalloc(size_t nmemb, size_t size)
{
	void *p;

	if (nmemb == 0 || size == 0)
		nmemb = size = 1;
	if ((p = calloc(nmemb, size)) == NULL)
		fatal("out of memory allocating %zu * %zu bytes", nmemb, size);
	return p;
}

void *
xreallocarray(void *ptr, size_t nmemb, size_t size)
{
	void *p;

	if (size != 0 && nmemb > SIZE_MAX / size)
		fatal("allocation overflow");
	if ((p = realloc(ptr, nmemb * size != 0 ? nmemb * size : 1)) == NULL)
		fatal("out of memory reallocating %zu * %zu bytes", nmemb, size);
	return p;
}

char *
xstrdup(const char *s)
{
	return xstrndup(s, strlen(s));
}

char *
xstrndup(const char *s, size_t n)
{
	char *p = xmalloc(n + 1);

	memcpy(p, s, n);
	p[n] = '\0';
	return p;
}

int
xasprintf(char **ret, const char *fmt, ...)
{
	va_list ap;
	int n;

	va_start(ap, fmt);
	n = vasprintf(ret, fmt, ap);
	va_end(ap);
	if (n < 0 || *ret == NULL)
		fatal("out of memory formatting string");
	return n;
}
