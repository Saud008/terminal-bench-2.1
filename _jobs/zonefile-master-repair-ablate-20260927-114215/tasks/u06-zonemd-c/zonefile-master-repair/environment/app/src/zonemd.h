#ifndef ZONEC_ZONEMD_H
#define ZONEC_ZONEMD_H

#include "zone.h"

#define ZONEMD_SCHEME_SIMPLE 1
#define ZONEMD_HASH_SHA384 1

/* Fills in the apex ZONEMD record, if the zone has one (see docs/zonemd.md).
 * Expects a finished zone: sorted, without duplicates, RRset TTLs settled. */
void zonemd_update(zone_t *z);

#endif
