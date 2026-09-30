#ifndef ZONEC_ZONE_H
#define ZONEC_ZONE_H

#include <stddef.h>
#include <stdint.h>

#include "buf.h"
#include "name.h"

typedef struct {
    dname_t owner;
    char *owner_text;
    uint16_t type;
    uint32_t ttl;
    unsigned char *rd;
    size_t rdlen;
    size_t seq;        /* position in input order */
} rr_t;

typedef struct {
    dname_t origin;
    rr_t *v;
    size_t n;
    size_t cap;
    int have_soa;
    uint32_t soa_minimum;
} zone_t;

void zone_init(zone_t *z, const dname_t *origin);
void zone_add(zone_t *z, const dname_t *owner, uint16_t type, uint32_t ttl,
              const unsigned char *rd, size_t rdlen);

/* Drops duplicate records, settles RRset TTLs and sorts the zone. */
void zone_finish(zone_t *z);
void zone_emit(const zone_t *z, buf_t *out);

#endif
