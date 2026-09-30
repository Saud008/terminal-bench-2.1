#ifndef ZONEC_PARSER_H
#define ZONEC_PARSER_H

#include "diag.h"
#include "lexer.h"
#include "name.h"
#include "ttl.h"
#include "zone.h"

#define INCLUDE_DEPTH_MAX 8

/* Parser state that directives and records read and update. */
typedef struct {
    zone_t *zone;
    dname_t origin;     /* current $ORIGIN */
    dname_t owner;      /* owner of the previous record */
    int have_owner;
    ttl_ctx_t ttl;
    int depth;          /* $INCLUDE nesting level */
} parse_ctx_t;

/* Parses one master file into ctx->zone. `from` is the $INCLUDE line that
 * named the file, or NULL for the top-level file. */
void parse_file(parse_ctx_t *ctx, const char *path, const srcpos_t *from);

/* Handles a $ORIGIN, $TTL or $INCLUDE entry (directives.c). */
void parse_directive(parse_ctx_t *ctx, const char *path, const lline_t *ll);

#endif
