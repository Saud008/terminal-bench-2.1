#ifndef ZONEC_RDATA_H
#define ZONEC_RDATA_H

#include <stddef.h>
#include <stdint.h>

#include "buf.h"
#include "diag.h"
#include "lexer.h"
#include "name.h"

enum {
    TYPE_A = 1,
    TYPE_NS = 2,
    TYPE_CNAME = 5,
    TYPE_SOA = 6,
    TYPE_PTR = 12,
    TYPE_MX = 15,
    TYPE_TXT = 16,
    TYPE_AAAA = 28,
    TYPE_SRV = 33,
    TYPE_CAA = 257,
};

/* Everything an RDATA parser needs besides its tokens. */
typedef struct {
    const dname_t *origin;
    const srcpos_t *pos;
    const char *type;
} rdctx_t;

typedef void (*rd_parse_fn)(const rdctx_t *cx, const token_t *tok, size_t n, buf_t *rd);
typedef void (*rd_format_fn)(const unsigned char *rd, size_t len, buf_t *out);

typedef struct {
    const char *name;
    uint16_t code;
    rd_parse_fn parse;
    rd_format_fn format;
} rrtype_t;

const rrtype_t *rrtype_by_name(const char *name);
const rrtype_t *rrtype_by_code(uint16_t code);

/* Helpers shared by the per-type parsers and formatters. */
void rd_expect(const rdctx_t *cx, size_t n, size_t want);
void rd_name(const rdctx_t *cx, const token_t *t, buf_t *rd);
uint32_t rd_number(const rdctx_t *cx, const token_t *t, uint32_t max, const char *field);
uint32_t rd_period(const rdctx_t *cx, const token_t *t, const char *field);
size_t rd_fmt_name(const unsigned char *rd, size_t len, size_t off, buf_t *out);
uint32_t rd_get16(const unsigned char *p);
uint32_t rd_get32(const unsigned char *p);

void rr_a_parse(const rdctx_t *cx, const token_t *tok, size_t n, buf_t *rd);
void rr_a_format(const unsigned char *rd, size_t len, buf_t *out);
void rr_aaaa_parse(const rdctx_t *cx, const token_t *tok, size_t n, buf_t *rd);
void rr_aaaa_format(const unsigned char *rd, size_t len, buf_t *out);
void rr_name_parse(const rdctx_t *cx, const token_t *tok, size_t n, buf_t *rd);
void rr_name_format(const unsigned char *rd, size_t len, buf_t *out);
void rr_mx_parse(const rdctx_t *cx, const token_t *tok, size_t n, buf_t *rd);
void rr_mx_format(const unsigned char *rd, size_t len, buf_t *out);
void rr_soa_parse(const rdctx_t *cx, const token_t *tok, size_t n, buf_t *rd);
void rr_soa_format(const unsigned char *rd, size_t len, buf_t *out);
uint32_t rr_soa_minimum(const unsigned char *rd, size_t len);
void rr_txt_parse(const rdctx_t *cx, const token_t *tok, size_t n, buf_t *rd);
void rr_txt_format(const unsigned char *rd, size_t len, buf_t *out);
void rr_srv_parse(const rdctx_t *cx, const token_t *tok, size_t n, buf_t *rd);
void rr_srv_format(const unsigned char *rd, size_t len, buf_t *out);
void rr_caa_parse(const rdctx_t *cx, const token_t *tok, size_t n, buf_t *rd);
void rr_caa_format(const unsigned char *rd, size_t len, buf_t *out);

#endif
