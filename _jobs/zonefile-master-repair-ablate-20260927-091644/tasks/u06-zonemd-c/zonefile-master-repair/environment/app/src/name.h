#ifndef ZONEC_NAME_H
#define ZONEC_NAME_H

#include "buf.h"

#define NAME_MAXWIRE 255
#define LABEL_MAX 63

/* A domain name in uncompressed wire form, root label included. Names are
 * always kept in canonical (lowercase) form. */
typedef struct {
    unsigned char wire[NAME_MAXWIRE];
    int len;
} dname_t;

extern const dname_t name_root;

/* Parses a name in presentation form. "@" is the origin, names ending in
 * "." are absolute, anything else is relative to origin. On failure *err
 * points to a short description and -1 is returned. */
int name_parse(const char *text, const dname_t *origin, dname_t *out, const char **err);

/* Reads a wire name starting at rd[off]; returns the offset after it or 0
 * if the data is malformed. */
size_t name_from_wire(const unsigned char *rd, size_t rdlen, size_t off, dname_t *out);

int name_equal(const dname_t *a, const dname_t *b);
int name_cmp_canonical(const dname_t *a, const dname_t *b);
int name_is_subdomain(const dname_t *child, const dname_t *parent);
void name_format(const dname_t *n, buf_t *out);

#endif
