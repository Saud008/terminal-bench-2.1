#include "hopcfg.h"

#include <errno.h>
#include <glob.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>

#define WHITESPACE " \t\r\n"

struct multistate {
	const char *key;
	int value;
};

static const struct multistate multistate_flag[] = {
	{ "true", 1 }, { "false", 0 }, { "yes", 1 }, { "no", 0 },
	{ NULL, -1 }
};
static const struct multistate multistate_strict_hostkey[] = {
	{ "true", STRICT_YES }, { "false", STRICT_OFF },
	{ "yes", STRICT_YES }, { "no", STRICT_OFF },
	{ "ask", STRICT_ASK }, { "off", STRICT_OFF },
	{ "accept-new", STRICT_NEW },
	{ NULL, -1 }
};
static const struct multistate multistate_controlmaster[] = {
	{ "true", CTL_YES }, { "yes", CTL_YES },
	{ "false", CTL_NO }, { "no", CTL_NO },
	{ "auto", CTL_AUTO }, { "ask", CTL_ASK }, { "autoask", CTL_AUTO_ASK },
	{ NULL, -1 }
};
static const struct multistate multistate_canonicalize[] = {
	{ "true", 1 }, { "false", 0 }, { "yes", 1 }, { "no", 0 },
	{ "always", 2 },
	{ NULL, -1 }
};

static const struct {
	const char *name;
	int level;
} log_levels[] = {
	{ "SILENT", LOG_QUIET }, { "QUIET", LOG_QUIET },
	{ "FATAL", LOG_FATAL }, { "ERROR", LOG_ERROR },
	{ "INFO", LOG_INFO }, { "VERBOSE", LOG_VERBOSE },
	{ "DEBUG", LOG_DEBUG1 }, { "DEBUG1", LOG_DEBUG1 },
	{ "DEBUG2", LOG_DEBUG2 }, { "DEBUG3", LOG_DEBUG3 },
	{ NULL, LOG_UNSET }
};

static int
parse_multistate_value(const char *arg, const struct multistate *m)
{
	int i;

	if (arg == NULL || *arg == '\0')
		return -1;
	for (i = 0; m[i].key != NULL; i++)
		if (strcasecmp(arg, m[i].key) == 0)
			return m[i].value;
	return -1;
}

static int
log_level_number(const char *name)
{
	int i;

	if (name != NULL)
		for (i = 0; log_levels[i].name != NULL; i++)
			if (strcasecmp(log_levels[i].name, name) == 0)
				return log_levels[i].level;
	return LOG_UNSET;
}

static int read_config_file_depth(const char *, const char *, const char *,
    Options *, int, int *, int *, int);

/*
 * Process one configuration line.  Values are only stored if they have not
 * been set already, so the first obtained value wins.  activep is NULL for
 * command-line (-o) options, which are always active.
 * Returns 0 on success, -1 on a bad line.
 */
int
process_config_line(Options *options, const char *host,
    const char *original_host, char *line, const char *filename,
    int linenum, int *activep, int flags, int *want_final_pass, int depth)
{
	char *str, **charptr, *keyword, *arg, *arg2;
	char **oav = NULL, **av, fwdarg[256];
	int oac = 0, ac, value, value2, *intptr, cmdline = 0, oactive, negated;
	int remotefwd, dynamicfwd, i, r, ret = -1;
	const struct multistate *multistate_ptr;
	struct strlist *list;
	struct forward fwd;
	enum opcode opcode;
	size_t len;
	glob_t gl;

	if (activep == NULL) {
		cmdline = 1;
		activep = &cmdline;
	}

	if ((len = strlen(line)) == 0)
		return 0;
	for (len--; len > 0; len--) {
		if (strchr(WHITESPACE "\f", line[len]) == NULL)
			break;
		line[len] = '\0';
	}

	str = line;
	if ((keyword = strdelim(&str)) == NULL)
		return 0;
	if (*keyword == '\0')
		keyword = strdelim(&str);
	if (keyword == NULL || !*keyword || *keyword == '\n' || *keyword == '#')
		return 0;
	lowercase(keyword);

	if (str != NULL)
		str += strspn(str, WHITESPACE);
	if (str == NULL || *str == '\0') {
		error("%s line %d: no argument after keyword \"%s\"",
		    filename, linenum, keyword);
		return -1;
	}
	opcode = lookup_keyword(keyword, options->ignored_unknown);
	if (argv_split(str, &oac, &oav, 1) != 0) {
		error("%s line %d: invalid quotes", filename, linenum);
		return -1;
	}
	ac = oac;
	av = oav;

	switch (opcode) {
	case oBadOption:
		error("%s: line %d: Bad configuration option: %s",
		    filename, linenum, keyword);
		goto out;

	case oIgnore:
	case oDeprecated:
	case oPassthrough:
	case oIgnoredUnknownOption:
		argv_consume(&ac);
		break;

	case oUnsupported:
		error("%s line %d: Unsupported option \"%s\"",
		    filename, linenum, keyword);
		argv_consume(&ac);
		break;

	case oConnectTimeout:
		intptr = &options->connection_timeout;
 parse_time:
		arg = argv_next(&ac, &av);
		if (!arg || *arg == '\0') {
			error("%s line %d: missing time value.",
			    filename, linenum);
			goto out;
		}
		if (strcmp(arg, "none") == 0)
			value = -1;
		else if ((value = convtime(arg)) == -1) {
			error("%s line %d: invalid time value.",
			    filename, linenum);
			goto out;
		}
		if (*activep && *intptr == -1)
			*intptr = value;
		break;

	case oServerAliveInterval:
		intptr = &options->server_alive_interval;
		goto parse_time;

	case oForwardAgent:
		intptr = &options->forward_agent;
		arg = argv_next(&ac, &av);
		if (!arg || *arg == '\0') {
			error("%s line %d: missing argument.",
			    filename, linenum);
			goto out;
		}
		value = parse_multistate_value(arg, multistate_flag);
		if (value != -1) {
			if (*activep && *intptr == -1)
				*intptr = value;
			break;
		}
		/* not a flag, so an agent socket path */
		if (*activep && *intptr == -1)
			*intptr = 1;
		if ((arg2 = dollar_expand(&r, arg)) == NULL || r) {
			error("%s line %d: Invalid environment expansion %s.",
			    filename, linenum, arg);
			goto out;
		}
		free(arg2);
		if (arg[0] == '$' && arg[1] != '{' && !valid_env_name(arg + 1)) {
			error("%s line %d: Invalid environment name %s.",
			    filename, linenum, arg);
			goto out;
		}
		if (*activep && options->forward_agent_sock_path == NULL)
			options->forward_agent_sock_path = xstrdup(arg);
		break;

	case oBatchMode:
		intptr = &options->batch_mode;
 parse_flag:
		multistate_ptr = multistate_flag;
 parse_multistate:
		arg = argv_next(&ac, &av);
		if ((value = parse_multistate_value(arg, multistate_ptr)) == -1) {
			error("%s line %d: unsupported option \"%s\".",
			    filename, linenum, arg ? arg : "");
			goto out;
		}
		if (*activep && *intptr == -1)
			*intptr = value;
		break;

	case oIdentitiesOnly:
		intptr = &options->identities_only;
		goto parse_flag;

	case oClearAllForwardings:
		intptr = &options->clear_forwardings;
		goto parse_flag;

	case oStrictHostKeyChecking:
		intptr = &options->strict_host_key_checking;
		multistate_ptr = multistate_strict_hostkey;
		goto parse_multistate;

	case oControlMaster:
		intptr = &options->control_master;
		multistate_ptr = multistate_controlmaster;
		goto parse_multistate;

	case oCanonicalizeHostname:
		arg = argv_next(&ac, &av);
		if ((value = parse_multistate_value(arg,
		    multistate_canonicalize)) == -1) {
			error("%s line %d: unsupported option \"%s\".",
			    filename, linenum, arg ? arg : "");
			goto out;
		}
		if (value != 0) {
			error("%s line %d: CanonicalizeHostname is not "
			    "supported", filename, linenum);
			goto out;
		}
		break;

	case oServerAliveCountMax:
		intptr = &options->server_alive_count_max;
		arg = argv_next(&ac, &av);
		if (atoi_err(arg, &value) != NULL) {
			error("%s line %d: integer value %s.",
			    filename, linenum, atoi_err(arg, &value));
			goto out;
		}
		if (*activep && *intptr == -1)
			*intptr = value;
		break;

	case oIdentityFile:
	case oCertificateFile:
		arg = argv_next(&ac, &av);
		if (!arg || *arg == '\0') {
			error("%s line %d: Missing argument.",
			    filename, linenum);
			goto out;
		}
		if (opcode == oIdentityFile)
			list = &options->identity_files;
		else
			list = &options->certificate_files;
		if (*activep) {
			if (list->n >= (opcode == oIdentityFile ?
			    MAX_IDENTITY_FILES : MAX_CERTIFICATE_FILES)) {
				error("%s line %d: Too many files specified.",
				    filename, linenum);
				goto out;
			}
			if (!strlist_contains(list, arg))
				strlist_append(list, arg);
		}
		break;

	case oUser:
		charptr = &options->user;
 parse_string:
		arg = argv_next(&ac, &av);
		if (!arg || *arg == '\0') {
			error("%s line %d: Missing argument.",
			    filename, linenum);
			goto out;
		}
		if (*activep && *charptr == NULL)
			*charptr = xstrdup(arg);
		break;

	case oHostname:
		charptr = &options->hostname;
		goto parse_string;

	case oHostKeyAlias:
		charptr = &options->host_key_alias;
		goto parse_string;

	case oControlPath:
		charptr = &options->control_path;
		goto parse_string;

	case oIgnoreUnknown:
		charptr = &options->ignored_unknown;
		goto parse_string;

	case oUserKnownHostsFile:
		list = &options->user_hostfiles;
		i = 0;
		value = list->n == 0;
		while ((arg = argv_next(&ac, &av)) != NULL) {
			if (*arg == '\0') {
				error("%s line %d: keyword %s empty argument",
				    filename, linenum, keyword);
				goto out;
			}
			if (strcasecmp(arg, "none") == 0 && (i > 0 || ac > 0)) {
				error("%s line %d: keyword %s \"none\" "
				    "argument must appear alone.",
				    filename, linenum, keyword);
				goto out;
			}
			i++;
			if (*activep && value) {
				if (list->n >= MAX_HOSTFILES) {
					error("%s line %d: too many %s "
					    "entries.", filename, linenum,
					    keyword);
					goto out;
				}
				strlist_append(list, arg);
			}
		}
		break;

	case oProxyCommand:
		charptr = &options->proxy_command;
		goto parse_command;

	case oRemoteCommand:
		charptr = &options->remote_command;
 parse_command:
		len = strspn(str, WHITESPACE "=");
		if (*activep && *charptr == NULL)
			*charptr = xstrdup(str + len);
		argv_consume(&ac);
		break;

	case oProxyJump:
		len = strspn(str, WHITESPACE "=");
		if (parse_jump(str + len, options, *activep) == -1) {
			error("%s line %d: Invalid ProxyJump \"%s\"",
			    filename, linenum, str + len);
			goto out;
		}
		argv_consume(&ac);
		break;

	case oPort:
		arg = argv_next(&ac, &av);
		if (!arg || *arg == '\0') {
			error("%s line %d: Missing argument.",
			    filename, linenum);
			goto out;
		}
		value = a2port(arg);
		if (value <= 0) {
			error("%s line %d: Bad port '%s'.",
			    filename, linenum, arg);
			goto out;
		}
		if (*activep && options->port == -1)
			options->port = value;
		break;

	case oLogLevel:
		arg = argv_next(&ac, &av);
		value = log_level_number(arg);
		if (value == LOG_UNSET) {
			error("%s line %d: unsupported log level '%s'",
			    filename, linenum, arg ? arg : "<NONE>");
			goto out;
		}
		if (*activep && options->log_level == LOG_UNSET)
			options->log_level = value;
		break;

	case oLocalForward:
	case oRemoteForward:
	case oDynamicForward:
		arg = argv_next(&ac, &av);
		if (!arg || *arg == '\0') {
			error("%s line %d: Missing argument.",
			    filename, linenum);
			goto out;
		}
		remotefwd = (opcode == oRemoteForward);
		dynamicfwd = (opcode == oDynamicForward);
		if (!dynamicfwd) {
			arg2 = argv_next(&ac, &av);
			if (arg2 == NULL || *arg2 == '\0') {
				if (remotefwd)
					dynamicfwd = 1;
				else {
					error("%s line %d: Missing target "
					    "argument.", filename, linenum);
					goto out;
				}
			} else
				snprintf(fwdarg, sizeof(fwdarg), "%s:%s",
				    arg, arg2);
		}
		if (dynamicfwd)
			snprintf(fwdarg, sizeof(fwdarg), "%s", arg);
		if (parse_forward(&fwd, fwdarg, dynamicfwd, remotefwd) == 0) {
			error("%s line %d: Bad forwarding specification.",
			    filename, linenum);
			goto out;
		}
		if (*activep)
			add_forward(remotefwd ? &options->remote_forwards :
			    &options->local_forwards, &fwd);
		else
			free_forward(&fwd);
		break;

	case oSendEnv:
		while ((arg = argv_next(&ac, &av)) != NULL) {
			if (*arg == '\0' || strchr(arg, '=') != NULL) {
				error("%s line %d: Invalid environment name.",
				    filename, linenum);
				goto out;
			}
			if (!*activep)
				continue;
			if (*arg == '-') {
				strlist_remove_matching(&options->send_env,
				    arg + 1);
				continue;
			}
			strlist_append(&options->send_env, arg);
		}
		break;

	case oSetEnv:
		value = options->setenv.n;
		while ((arg = argv_next(&ac, &av)) != NULL) {
			if (strchr(arg, '=') == NULL) {
				error("%s line %d: Invalid SetEnv.",
				    filename, linenum);
				goto out;
			}
			if (!*activep || value != 0)
				continue;
			len = strchr(arg, '=') - arg;
			for (i = 0; i < options->setenv.n; i++) {
				if (strncmp(options->setenv.v[i], arg, len) == 0 &&
				    options->setenv.v[i][len] == '=')
					break;
			}
			if (i < options->setenv.n)
				continue;
			strlist_append(&options->setenv, arg);
		}
		break;

	case oControlPersist:
		intptr = &options->control_persist;
		arg = argv_next(&ac, &av);
		if (!arg || *arg == '\0') {
			error("%s line %d: Missing ControlPersist argument.",
			    filename, linenum);
			goto out;
		}
		value = 0;
		value2 = 0;
		if (strcmp(arg, "no") == 0 || strcmp(arg, "false") == 0)
			value = 0;
		else if (strcmp(arg, "yes") == 0 || strcmp(arg, "true") == 0)
			value = 1;
		else if ((value2 = convtime(arg)) >= 0)
			value = 1;
		else {
			error("%s line %d: Bad ControlPersist argument.",
			    filename, linenum);
			goto out;
		}
		if (*activep && *intptr == -1) {
			*intptr = value;
			options->control_persist_timeout = value2;
		}
		break;

	case oHost:
		if (cmdline) {
			error("Host directive not supported as a command-line "
			    "option");
			goto out;
		}
		*activep = 0;
		while ((arg = argv_next(&ac, &av)) != NULL) {
			if (*arg == '\0') {
				error("%s line %d: keyword %s empty argument",
				    filename, linenum, keyword);
				goto out;
			}
			if ((flags & CONF_NEVERMATCH) != 0) {
				argv_consume(&ac);
				break;
			}
			negated = *arg == '!';
			if (negated)
				arg++;
			if (match_pattern(host, arg)) {
				if (negated) {
					*activep = 0;
					argv_consume(&ac);
					break;
				}
				*activep = 1;
			}
		}
		break;

	case oMatch:
		if (cmdline) {
			error("Host directive not supported as a command-line "
			    "option");
			goto out;
		}
		value = match_cfg_line(options, &str, host, original_host,
		    flags & CONF_FINAL, want_final_pass, filename, linenum);
		if (value < 0) {
			error("%s line %d: Bad Match condition", filename,
			    linenum);
			goto out;
		}
		*activep = (flags & CONF_NEVERMATCH) ? 0 : value;
		if (str == NULL || *str == '\0')
			argv_consume(&ac);
		break;

	case oInclude:
		if (cmdline) {
			error("Include directive not supported as a "
			    "command-line option");
			goto out;
		}
		value = 0;
		while ((arg = argv_next(&ac, &av)) != NULL) {
			if (*arg == '\0') {
				error("%s line %d: keyword %s empty argument",
				    filename, linenum, keyword);
				goto out;
			}
			if (*arg == '~' && (flags & CONF_USER) == 0) {
				error("%s line %d: bad include path %s.",
				    filename, linenum, arg);
				goto out;
			}
			if (*arg != '/' && *arg != '~')
				xasprintf(&arg2, "%s/%s", (flags & CONF_USER) ?
				    "~/.ssh" : "/etc/ssh", arg);
			else
				arg2 = xstrdup(arg);
			memset(&gl, 0, sizeof(gl));
			r = glob(arg2, GLOB_TILDE, NULL, &gl);
			if (r == GLOB_NOMATCH) {
				free(arg2);
				continue;
			} else if (r != 0) {
				error("%s line %d: glob failed for %s.",
				    filename, linenum, arg2);
				free(arg2);
				goto out;
			}
			free(arg2);
			oactive = *activep;
			for (i = 0; i < (int)gl.gl_pathc; i++) {
				r = read_config_file_depth(gl.gl_pathv[i],
				    host, original_host, options,
				    flags | (oactive ? 0 : CONF_NEVERMATCH),
				    activep, want_final_pass, depth + 1);
				if (r != 1 && errno != ENOENT) {
					error("Can't open user config file "
					    "%.100s: %.100s", gl.gl_pathv[i],
					    strerror(errno));
					globfree(&gl);
					goto out;
				}
				*activep = oactive;
				if (r != 1)
					value = -1;
			}
			globfree(&gl);
		}
		if (value != 0)
			ret = value;
		break;

	default:
		error("%s line %d: Unimplemented opcode %d",
		    filename, linenum, opcode);
		goto out;
	}

	if (ac > 0) {
		error("%s line %d: keyword %s extra arguments at end of line",
		    filename, linenum, keyword);
		goto out;
	}
	ret = 0;
 out:
	argv_free(oav, oac);
	return ret;
}

static int
read_config_file_depth(const char *filename, const char *host,
    const char *original_host, Options *options, int flags, int *activep,
    int *want_final_pass, int depth)
{
	FILE *f;
	char *line = NULL;
	size_t linesize = 0;
	int linenum = 0, bad_options = 0;

	if (depth < 0 || depth > MAX_INCLUDE_DEPTH)
		fatal("Too many recursive configuration includes");

	if ((f = fopen(filename, "r")) == NULL)
		return 0;

	while (getline(&line, &linesize, f) != -1) {
		linenum++;
		if (process_config_line(options, host, original_host, line,
		    filename, linenum, activep, flags, want_final_pass,
		    depth) != 0)
			bad_options++;
	}
	free(line);
	fclose(f);
	if (bad_options > 0)
		fatal("%s: terminating, %d bad configuration options",
		    filename, bad_options);
	return 1;
}

/* Returns 1 if the file was read, 0 if it could not be opened. */
int
read_config_file(const char *filename, const char *host,
    const char *original_host, Options *options, int flags,
    int *want_final_pass)
{
	int active = 1;

	return read_config_file_depth(filename, host, original_host, options,
	    flags, &active, want_final_pass, 0);
}
