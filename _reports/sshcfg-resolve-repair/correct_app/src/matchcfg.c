#include "hopcfg.h"

#include <stdlib.h>
#include <string.h>
#include <strings.h>

/*
 * Evaluate the criteria of a Match line.  host is the name the current
 * pass matches against, original_host the destination as given on the
 * command line.  Returns 1 if every criterion holds, 0 if not and -1 on a
 * malformed line.
 */
int
match_cfg_line(Options *options, char **condition, const char *host,
    const char *original_host, int final_pass, int *want_final_pass,
    const char *filename, int linenum)
{
	char *arg, *oattrib, *attrib, *cp = *condition, *target;
	const char *ruser;
	int r, result = 1, attributes = 0, negate;
	struct expand_key keys[2] = { { 'h', host }, { '\0', NULL } };

	ruser = options->user == NULL ? hop_pw->pw_name : options->user;
	if (final_pass)
		target = xstrdup(options->hostname);
	else if (options->hostname != NULL)
		target = percent_expand(options->hostname, keys);
	else
		target = xstrdup(host);

	while ((oattrib = attrib = strdelim(&cp)) && *attrib != '\0') {
		if (*attrib == '#') {
			cp = NULL;
			break;
		}
		arg = NULL;
		if ((negate = attrib[0] == '!'))
			attrib++;
		if (strcasecmp(attrib, "all") == 0) {
			if (attributes > 1 || ((arg = strdelim(&cp)) != NULL &&
			    *arg != '\0' && *arg != '#')) {
				error("%s line %d: '%s' cannot be combined "
				    "with other Match attributes",
				    filename, linenum, oattrib);
				result = -1;
				goto out;
			}
			if (arg != NULL && *arg == '#')
				cp = NULL;
			if (result)
				result = negate ? 0 : 1;
			goto out;
		}
		attributes++;
		if (strcasecmp(attrib, "canonical") == 0 ||
		    strcasecmp(attrib, "final") == 0) {
			if (strcasecmp(attrib, "final") == 0 &&
			    want_final_pass != NULL)
				*want_final_pass = 1;
			r = !!final_pass;
			if (r == (negate ? 1 : 0))
				result = 0;
			continue;
		}
		if ((arg = strdelim(&cp)) == NULL || *arg == '\0' ||
		    *arg == '#') {
			error("Missing Match criteria for %s", attrib);
			result = -1;
			goto out;
		}
		if (strcasecmp(attrib, "host") == 0) {
			r = match_hostname(target, arg) == 1;
			if (r == (negate ? 1 : 0))
				result = 0;
		} else if (strcasecmp(attrib, "originalhost") == 0) {
			r = match_hostname(original_host, arg) == 1;
			if (r == (negate ? 1 : 0))
				result = 0;
		} else if (strcasecmp(attrib, "user") == 0) {
			r = match_pattern_list(ruser, arg, 0) == 1;
			if (r == (negate ? 1 : 0))
				result = 0;
		} else if (strcasecmp(attrib, "localuser") == 0) {
			r = match_pattern_list(hop_pw->pw_name, arg, 0) == 1;
			if (r == (negate ? 1 : 0))
				result = 0;
		} else if (strcasecmp(attrib, "exec") == 0) {
			error("%s line %d: Match exec is not supported",
			    filename, linenum);
			result = -1;
			goto out;
		} else {
			error("Unsupported Match attribute %s", attrib);
			result = -1;
			goto out;
		}
	}
	if (attributes == 0) {
		error("One or more attributes required for Match");
		result = -1;
	}
 out:
	*condition = cp;
	free(target);
	return result;
}
