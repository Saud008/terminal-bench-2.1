#ifndef ZONEC_DIAG_H
#define ZONEC_DIAG_H

/* A position in a master file, reported as FILE:LINE. */
typedef struct {
    const char *file;
    int line;
} srcpos_t;

/* All diagnostics are fatal: the message goes to stderr and zonec exits
 * with status 1 before anything is written to stdout. */
_Noreturn void fail_at(const srcpos_t *pos, const char *fmt, ...);
_Noreturn void fail_file(const char *file, const char *fmt, ...);

/* Command line problems exit with status 2. */
_Noreturn void fail_usage(const char *fmt, ...);

#endif
