#include "hopcfg.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>

static void
vlog(const char *fmt, va_list ap)
{
	fputs("hopcfg: ", stderr);
	vfprintf(stderr, fmt, ap);
	fputc('\n', stderr);
}

void
error(const char *fmt, ...)
{
	va_list ap;

	va_start(ap, fmt);
	vlog(fmt, ap);
	va_end(ap);
}

void
fatal(const char *fmt, ...)
{
	va_list ap;

	va_start(ap, fmt);
	vlog(fmt, ap);
	va_end(ap);
	fflush(stdout);
	exit(255);
}
