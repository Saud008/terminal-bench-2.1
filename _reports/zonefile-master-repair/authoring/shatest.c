#include "sha384.h"

#include <stdio.h>

int main(void)
{
    unsigned char buf[4096], out[48];
    size_t n = fread(buf, 1, sizeof buf, stdin);
    sha384_ctx c;
    sha384_init(&c);
    sha384_update(&c, buf, n);
    sha384_final(&c, out);
    for (int i = 0; i < 48; i++)
        printf("%02x", out[i]);
    putchar('\n');
    return 0;
}
