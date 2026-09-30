#include "name.h"

#include <string.h>

const dname_t name_root = { { 0 }, 1 };

static int is_digit(char c)
{
    return c >= '0' && c <= '9';
}

static void name_lower(dname_t *n)
{
    int i = 0;
    while (n->wire[i]) {
        int len = n->wire[i];
        for (int j = i + 1; j <= i + len; j++)
            if (n->wire[j] >= 'A' && n->wire[j] <= 'Z')
                n->wire[j] = (unsigned char)(n->wire[j] - 'A' + 'a');
        i += len + 1;
    }
}

int name_parse(const char *text, const dname_t *origin, dname_t *out, const char **err)
{
    unsigned char w[NAME_MAXWIRE];
    int wl = 0;
    int absolute = 0;
    const char *p = text;

    if (strcmp(text, "@") == 0) {
        *out = *origin;
        return 0;
    }
    if (strcmp(text, ".") == 0) {
        *out = name_root;
        return 0;
    }

    while (*p) {
        int lenpos = wl++;
        int lablen = 0;

        while (*p && *p != '.') {
            unsigned c;
            if (*p == '\\') {
                if (is_digit(p[1])) {
                    if (!is_digit(p[2]) || !is_digit(p[3])) {
                        *err = "bad escape in name";
                        return -1;
                    }
                    c = (unsigned)(p[1] - '0') * 100 + (unsigned)(p[2] - '0') * 10 + (unsigned)(p[3] - '0');
                    if (c > 255) {
                        *err = "bad escape in name";
                        return -1;
                    }
                    p += 4;
                } else if (p[1]) {
                    c = (unsigned char)p[1];
                    p += 2;
                } else {
                    *err = "bad escape in name";
                    return -1;
                }
            } else {
                c = (unsigned char)*p++;
            }
            if (lablen == LABEL_MAX) {
                *err = "label too long";
                return -1;
            }
            if (wl >= NAME_MAXWIRE - 1) {
                *err = "name too long";
                return -1;
            }
            w[wl++] = (unsigned char)c;
            lablen++;
        }
        if (lablen == 0) {
            *err = "empty label";
            return -1;
        }
        w[lenpos] = (unsigned char)lablen;
        if (*p == '.') {
            p++;
            if (*p == '\0')
                absolute = 1;
        }
    }

    if (absolute) {
        w[wl++] = 0;
    } else {
        if (wl + origin->len > NAME_MAXWIRE) {
            *err = "name too long";
            return -1;
        }
        memcpy(w + wl, origin->wire, (size_t)origin->len);
        wl += origin->len;
    }

    memcpy(out->wire, w, (size_t)wl);
    out->len = wl;
    name_lower(out);
    return 0;
}

size_t name_from_wire(const unsigned char *rd, size_t rdlen, size_t off, dname_t *out)
{
    int wl = 0;
    for (;;) {
        if (off >= rdlen)
            return 0;
        unsigned len = rd[off];
        if (len > LABEL_MAX || off + 1 + len > rdlen || wl + 1 + (int)len > NAME_MAXWIRE)
            return 0;
        memcpy(out->wire + wl, rd + off, len + 1);
        wl += (int)len + 1;
        off += len + 1;
        if (len == 0)
            break;
    }
    out->len = wl;
    return off;
}

int name_equal(const dname_t *a, const dname_t *b)
{
    return a->len == b->len && memcmp(a->wire, b->wire, (size_t)a->len) == 0;
}

static int label_offsets(const dname_t *n, int *off)
{
    int k = 0, i = 0;
    while (n->wire[i]) {
        off[k++] = i;
        i += n->wire[i] + 1;
    }
    return k;
}

int name_cmp_canonical(const dname_t *a, const dname_t *b)
{
    int oa[NAME_MAXWIRE / 2], ob[NAME_MAXWIRE / 2];
    int ka = label_offsets(a, oa);
    int kb = label_offsets(b, ob);

    while (ka > 0 && kb > 0) {
        const unsigned char *la = a->wire + oa[--ka];
        const unsigned char *lb = b->wire + ob[--kb];
        int n = la[0] < lb[0] ? la[0] : lb[0];
        int r = memcmp(la + 1, lb + 1, (size_t)n);
        if (r)
            return r < 0 ? -1 : 1;
        if (la[0] != lb[0])
            return la[0] < lb[0] ? -1 : 1;
    }
    if (ka)
        return 1;
    if (kb)
        return -1;
    return 0;
}

int name_is_subdomain(const dname_t *child, const dname_t *parent)
{
    int i = 0;
    for (;;) {
        if (child->len - i == parent->len &&
            memcmp(child->wire + i, parent->wire, (size_t)parent->len) == 0)
            return 1;
        if (child->wire[i] == 0)
            return 0;
        i += child->wire[i] + 1;
    }
}

void name_format(const dname_t *n, buf_t *out)
{
    int i = 0;
    if (n->wire[0] == 0) {
        buf_put8(out, '.');
        return;
    }
    while (n->wire[i]) {
        int len = n->wire[i];
        for (int j = i + 1; j <= i + len; j++) {
            unsigned char c = n->wire[j];
            if (strchr(".\\\"();@$", c) && c != '\0') {
                buf_put8(out, '\\');
                buf_put8(out, c);
            } else if (c <= 0x20 || c >= 0x7f) {
                buf_printf(out, "\\%03u", c);
            } else {
                buf_put8(out, c);
            }
        }
        buf_put8(out, '.');
        i += len + 1;
    }
}
