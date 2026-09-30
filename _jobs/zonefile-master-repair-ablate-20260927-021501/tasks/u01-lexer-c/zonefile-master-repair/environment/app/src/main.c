#include "buf.h"
#include "diag.h"
#include "name.h"
#include "parser.h"
#include "zone.h"

#include <stdio.h>
#include <string.h>

static void usage(FILE *fp)
{
    fputs("usage: zonec -o ORIGIN FILE\n"
          "Compile a DNS master file into canonical record listing on stdout.\n",
          fp);
}

int main(int argc, char **argv)
{
    const char *origin_text = NULL, *file = NULL, *err = NULL;
    dname_t origin;
    zone_t zone;
    parse_ctx_t ctx;
    buf_t out;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-o") == 0) {
            if (++i >= argc)
                fail_usage("-o needs an argument");
            origin_text = argv[i];
        } else if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            usage(stdout);
            return 0;
        } else if (argv[i][0] == '-' && argv[i][1] != '\0') {
            fail_usage("unknown option %s", argv[i]);
        } else if (!file) {
            file = argv[i];
        } else {
            fail_usage("only one FILE may be given");
        }
    }
    if (!origin_text || !file)
        fail_usage("missing %s", origin_text ? "FILE" : "-o ORIGIN");
    if (name_parse(origin_text, &name_root, &origin, &err))
        fail_usage("bad origin %s: %s", origin_text, err);

    zone_init(&zone, &origin);
    memset(&ctx, 0, sizeof ctx);
    ctx.zone = &zone;
    ctx.origin = origin;

    parse_file(&ctx, file, NULL);
    if (!zone.have_soa)
        fail_file(file, "no SOA record at the zone apex");

    zone_finish(&zone);
    buf_init(&out);
    zone_emit(&zone, &out);
    fwrite(out.data, 1, out.len, stdout);
    buf_free(&out);
    return fflush(stdout) == 0 ? 0 : 1;
}
