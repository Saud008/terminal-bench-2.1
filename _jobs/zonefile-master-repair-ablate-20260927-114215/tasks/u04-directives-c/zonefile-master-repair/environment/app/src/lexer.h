#ifndef ZONEC_LEXER_H
#define ZONEC_LEXER_H

#include <stddef.h>

/* A token keeps its presentation text: escapes are left undecoded so that
 * names and character-strings can apply their own rules. For quoted tokens
 * the surrounding quotes are removed. */
typedef struct {
    char *text;
    int quoted;
} token_t;

/* One logical entry: a physical line, or several joined by parentheses. */
typedef struct {
    token_t *v;
    size_t n;
    size_t cap;
    int line;     /* physical line the entry starts on */
    int indented; /* entry starts with a blank or tab (no owner field) */
} lline_t;

typedef struct lexer lexer_t;

lexer_t *lexer_open(const char *path);
void lexer_close(lexer_t *lx);
const char *lexer_path(const lexer_t *lx);

/* Reads the next non-empty entry. Returns 1, or 0 at end of file. */
int lexer_next(lexer_t *lx, lline_t *ll);

void lline_init(lline_t *ll);
void lline_clear(lline_t *ll);

#endif
