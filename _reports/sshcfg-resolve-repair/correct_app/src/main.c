#include "hopcfg.h"

#include <netdb.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <unistd.h>

struct passwd *hop_pw;

static Options options;
static char *config;

static void
usage(void)
{
	fprintf(stderr,
	    "usage: hopcfg [-F configfile] [-l login_name] [-o option]\n"
	    "              [-p port] destination\n");
	exit(255);
}

static struct passwd *
pwcopy(const struct passwd *pw)
{
	struct passwd *copy = xcalloc(1, sizeof(*copy));

	copy->pw_name = xstrdup(pw->pw_name);
	copy->pw_uid = pw->pw_uid;
	copy->pw_gid = pw->pw_gid;
	copy->pw_dir = xstrdup(pw->pw_dir);
	copy->pw_shell = xstrdup(pw->pw_shell ? pw->pw_shell : "");
	return copy;
}

static void
process_config_files(const char *host, const char *host_arg, int final_pass,
    int *want_final_pass)
{
	char *path;
	int flags = CONF_USER | (final_pass ? CONF_FINAL : 0);

	if (config != NULL) {
		if (strcasecmp(config, "none") != 0 &&
		    !read_config_file(config, host, host_arg, &options, flags,
		    want_final_pass))
			fatal("Can't open user config file %.100s", config);
		return;
	}
	xasprintf(&path, "%s/.ssh/config", hop_pw->pw_dir);
	(void)read_config_file(path, host, host_arg, &options, flags,
	    want_final_pass);
	free(path);
}

static char *
expand_path(const char *s, const struct expand_key *keys)
{
	char *t, *r;

	t = tilde_expand_filename(s);
	r = percent_dollar_expand(t, keys);
	free(t);
	return r;
}

int
main(int argc, char **argv)
{
	struct expand_key keys[9];
	struct passwd *pw;
	char *host = NULL, *line, *cp, *p, *tuser;
	char portstr[16], uidstr[32], canon[NI_MAXHOST];
	int ch, i, tport, want_final_pass = 0, jumpport, port;
	const char *jumpuser, *keyalias;

	if ((pw = getpwuid(getuid())) == NULL)
		fatal("No user exists for uid %lu", (unsigned long)getuid());
	hop_pw = pwcopy(pw);

	initialize_options(&options);

	while ((ch = getopt(argc, argv, "F:l:o:p:")) != -1) {
		switch (ch) {
		case 'F':
			config = optarg;
			break;
		case 'l':
			if (options.user == NULL)
				options.user = xstrdup(optarg);
			break;
		case 'p':
			if (options.port == -1) {
				options.port = a2port(optarg);
				if (options.port <= 0)
					fatal("Bad port '%s'", optarg);
			}
			break;
		case 'o':
			line = xstrdup(optarg);
			if (process_config_line(&options, "", "", line,
			    "command-line", 0, NULL, CONF_USER, NULL, 0) != 0)
				exit(255);
			free(line);
			break;
		default:
			usage();
		}
	}
	argc -= optind;
	argv += optind;
	if (argc != 1)
		usage();

	switch (parse_ssh_uri(argv[0], &tuser, &host, &tport)) {
	case -1:
		usage();
		break;
	case 0:
		if (options.user == NULL)
			options.user = tuser;
		else
			free(tuser);
		if (options.port == -1 && tport != -1)
			options.port = tport;
		break;
	default:
		p = xstrdup(argv[0]);
		if ((cp = strrchr(p, '@')) != NULL) {
			if (cp == p)
				usage();
			*cp++ = '\0';
			if (options.user == NULL)
				options.user = xstrdup(p);
			host = xstrdup(cp);
		} else
			host = xstrdup(p);
		free(p);
		break;
	}

	if (options.user != NULL && !valid_ruser(options.user))
		fatal("remote username contains invalid characters");
	if (!valid_hostname(host))
		fatal("hostname contains invalid characters");

	options.host_arg = xstrdup(host);

	process_config_files(host, options.host_arg, 0, &want_final_pass);

	if (options.hostname != NULL) {
		keys[0] = (struct expand_key){ 'h', host };
		keys[1] = (struct expand_key){ '\0', NULL };
		cp = percent_expand(options.hostname, keys);
		free(host);
		host = cp;
		free(options.hostname);
		options.hostname = xstrdup(host);
	}

	if (!is_addr(host))
		lowercase(host);
	else if (canonical_addr(host, canon, sizeof(canon)) &&
	    strcasecmp(host, canon) != 0) {
		free(host);
		host = xstrdup(canon);
	}

	if (want_final_pass) {
		free(options.hostname);
		options.hostname = xstrdup(host);
		process_config_files(host, options.host_arg, 1, NULL);
	}

	fill_default_options(&options);

	if (options.user == NULL)
		options.user = xstrdup(hop_pw->pw_name);

	if (options.jump_host != NULL) {
		port = options.port <= 0 ? DEFAULT_SSH_PORT : options.port;
		jumpport = options.jump_port <= 0 ?
		    DEFAULT_SSH_PORT : options.jump_port;
		jumpuser = options.jump_user == NULL ?
		    options.user : options.jump_user;
		if (strcmp(options.jump_host, host) == 0 && port == jumpport &&
		    strcmp(options.user, jumpuser) == 0)
			fatal("jumphost loop via %s", options.jump_host);
	}

	if (options.port == 0)
		options.port = DEFAULT_SSH_PORT;
	if (options.host_key_alias != NULL)
		lowercase(options.host_key_alias);

	snprintf(portstr, sizeof(portstr), "%d", options.port);
	snprintf(uidstr, sizeof(uidstr), "%llu",
	    (unsigned long long)hop_pw->pw_uid);
	keyalias = options.host_key_alias ?
	    options.host_key_alias : options.host_arg;
	i = 0;
	keys[i++] = (struct expand_key){ 'i', uidstr };
	keys[i++] = (struct expand_key){ 'k', keyalias };
	keys[i++] = (struct expand_key){ 'n', options.host_arg };
	keys[i++] = (struct expand_key){ 'p', portstr };
	keys[i++] = (struct expand_key){ 'd', hop_pw->pw_dir };
	keys[i++] = (struct expand_key){ 'h', host };
	keys[i++] = (struct expand_key){ 'r', options.user };
	keys[i++] = (struct expand_key){ 'u', hop_pw->pw_name };
	keys[i] = (struct expand_key){ '\0', NULL };

	if (options.remote_command != NULL) {
		cp = options.remote_command;
		options.remote_command = percent_expand(cp, keys);
		free(cp);
	}
	if (options.control_path != NULL) {
		cp = options.control_path;
		options.control_path = expand_path(cp, keys);
		free(cp);
	}
	if (options.forward_agent_sock_path != NULL) {
		cp = options.forward_agent_sock_path;
		options.forward_agent_sock_path = expand_path(cp, keys);
		free(cp);
	}
	if (options.user_hostfiles.n > 0 &&
	    strcasecmp(options.user_hostfiles.v[0], "none") == 0) {
		if (options.user_hostfiles.n > 1)
			fatal("Invalid UserKnownHostsFiles: \"none\" "
			    "appears with other entries");
		strlist_clear(&options.user_hostfiles);
	}
	for (i = 0; i < options.user_hostfiles.n; i++) {
		cp = options.user_hostfiles.v[i];
		options.user_hostfiles.v[i] = expand_path(cp, keys);
		free(cp);
	}
	for (i = 0; i < options.local_forwards.n; i++) {
		struct forward *f = &options.local_forwards.v[i];

		if (f->listen_path != NULL) {
			cp = f->listen_path;
			f->listen_path = percent_expand(cp, keys);
			free(cp);
		}
		if (f->connect_path != NULL) {
			cp = f->connect_path;
			f->connect_path = percent_expand(cp, keys);
			free(cp);
		}
	}
	for (i = 0; i < options.remote_forwards.n; i++) {
		struct forward *f = &options.remote_forwards.v[i];

		if (f->listen_path != NULL) {
			cp = f->listen_path;
			f->listen_path = percent_expand(cp, keys);
			free(cp);
		}
		if (f->connect_path != NULL) {
			cp = f->connect_path;
			f->connect_path = percent_expand(cp, keys);
			free(cp);
		}
	}

	dump_client_config(&options, host);
	return 0;
}
