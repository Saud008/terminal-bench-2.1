#include "hopcfg.h"

#include <stdlib.h>
#include <string.h>
#include <strings.h>

static int
parse_one_hop(const char *spec, char **user, char **host, int *port)
{
	int r;

	r = parse_ssh_uri(spec, user, host, port);
	if (r == -1 || (r == 1 &&
	    parse_user_host_port(spec, user, host, port) != 0))
		return -1;
	return 0;
}

/*
 * Parse a ProxyJump value: "none" or a comma-separated list of
 * [user@]host[:port] / ssh:// hops.  The last hop becomes the jump host
 * and everything before it is kept verbatim as the extra jump chain.
 * Every hop is syntax-checked even when the line is not active.
 */
int
parse_jump(const char *s, Options *o, int active)
{
	char *orig = NULL, *sdup = NULL, *cp;
	char *tmp_user = NULL, *tmp_host = NULL, *host = NULL, *user = NULL;
	int ret = -1, tmp_port = -1, port = -1, first = 1;

	if (strcasecmp(s, "none") == 0) {
		if (active && o->jump_host == NULL) {
			o->jump_host = xstrdup("none");
			o->jump_port = 0;
		}
		return 0;
	}

	orig = xstrdup(s);
	if ((cp = strchr(orig, '#')) != NULL)
		*cp = '\0';
	rtrim(orig);

	active &= o->proxy_command == NULL && o->jump_host == NULL;
	sdup = xstrdup(orig);
	do {
		if ((cp = strrchr(sdup, ',')) == NULL)
			cp = sdup;
		else
			*cp++ = '\0';

		if (parse_one_hop(cp, &tmp_user, &tmp_host, &tmp_port) != 0)
			goto out;
		if (first) {
			user = tmp_user;
			host = tmp_host;
			port = tmp_port;
			tmp_user = tmp_host = NULL;
		}
		first = 0;
		free(tmp_user);
		free(tmp_host);
		tmp_user = tmp_host = NULL;
		tmp_port = -1;
	} while (cp != sdup);

	if (active) {
		o->jump_user = user;
		o->jump_host = host;
		o->jump_port = port;
		o->proxy_command = xstrdup("none");
		user = host = NULL;
		if ((cp = strrchr(orig, ',')) != NULL) {
			o->jump_extra = xstrdup(orig);
			o->jump_extra[cp - orig] = '\0';
		}
	}
	ret = 0;
 out:
	free(orig);
	free(sdup);
	free(tmp_user);
	free(tmp_host);
	free(user);
	free(host);
	return ret;
}
