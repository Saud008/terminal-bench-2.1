#include "diag.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>

void fail_at(const srcpos_t *pos, const char *fmt, ...)
{
    va_list ap;
    fprintf(stderr, "%s:%d: ", pos->file, pos->line);
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);
    fputc('\n', stderr);
    exit(1);
}

void fail_file(const char *file, const char *fmt, ...)
{
    va_list ap;
    fprintf(stderr, "%s: ", file);
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);
    fputc('\n', stderr);
    exit(1);
}

void fail_usage(const char *fmt, ...)
{
    va_list ap;
    fputs("zonec: ", stderr);
    va_start(ap, fmt);
    vfprintf(stderr, fmt, ap);
    va_end(ap);
    fputs("\nusage: zonec -o ORIGIN FILE\n", stderr);
    exit(2);
}
