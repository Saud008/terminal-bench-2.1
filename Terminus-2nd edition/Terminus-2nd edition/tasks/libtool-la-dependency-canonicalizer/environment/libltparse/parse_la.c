#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void trim(char *s) {
    size_t n = strlen(s);
    while (n > 0 && (s[n - 1] == '\n' || s[n - 1] == '\r' || s[n - 1] == ' ')) {
        s[--n] = '\0';
    }
}

static void emit(const char *key, const char *val) {
    printf("%s=%s\n", key, val);
}

int main(int argc, char **argv) {
    if (argc != 2) {
        fprintf(stderr, "usage: ltparse file.la\n");
        return 2;
    }
    FILE *fp = fopen(argv[1], "r");
    if (!fp) {
        perror("fopen");
        return 1;
    }
    char line[4096];
    while (fgets(line, sizeof line, fp)) {
        trim(line);
        if (line[0] == '\0' || line[0] == '#') {
            continue;
        }
        char *eq = strchr(line, '=');
        if (!eq) {
            continue;
        }
        *eq = '\0';
        char *val = eq + 1;
        while (*val == ' ') {
            val++;
        }
        size_t len = strlen(val);
        if (len >= 2 && val[0] == '\'' && val[len - 1] == '\'') {
            val[len - 1] = '\0';
            val++;
        }
        emit(line, val);
    }
    fclose(fp);
    return 0;
}
