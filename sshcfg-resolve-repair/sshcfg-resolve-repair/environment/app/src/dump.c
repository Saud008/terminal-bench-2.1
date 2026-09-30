#include "hopcfg.h"

#include <stdio.h>
#include <string.h>

static const char *
fmt_flag(int v)
{
	switch (v) {
	case 0:
		return "no";
	case 1:
		return "yes";
	default:
		return "UNKNOWN";
	}
}

static const char *
fmt_strict(int v)
{
	switch (v) {
	case STRICT_YES:
		return "true";
	case STRICT_OFF:
		return "false";
	case STRICT_ASK:
		return "ask";
	case STRICT_NEW:
		return "accept-new";
	default:
		return "UNKNOWN";
	}
}

static const char *
fmt_controlmaster(int v)
{
	switch (v) {
	case CTL_YES:
		return "true";
	case CTL_NO:
		return "false";
	case CTL_AUTO:
		return "auto";
	case CTL_ASK:
		return "ask";
	case CTL_AUTO_ASK:
		return "autoask";
	default:
		return "UNKNOWN";
	}
}

static const char *
fmt_loglevel(int v)
{
	static const char *names[] = {
		"QUIET", "FATAL", "ERROR", "INFO", "VERBOSE",
		"DEBUG", "DEBUG2", "DEBUG3"
	};

	if (v < 0 || v > LOG_DEBUG3)
		return NULL;
	return names[v];
}

static void
dump_string(const char *name, const char *val)
{
	if (val != NULL)
		printf("%s %s\n", name, val);
}

static void
dump_strarray(const char *name, const struct strlist *l)
{
	int i;

	for (i = 0; i < l->n; i++)
		printf("%s %s\n", name, l->v[i]);
}

static void
dump_strarray_oneline(const char *name, const struct strlist *l)
{
	int i;

	printf("%s", name);
	if (l->n == 0)
		printf(" none");
	for (i = 0; i < l->n; i++)
		printf(" %s", l->v[i]);
	printf("\n");
}

static void
dump_endpoint(const char *host, int port, const char *path)
{
	if (port == PORT_STREAMLOCAL)
		printf(" %s", path);
	else if (host == NULL)
		printf(" %d", port);
	else
		printf(" [%s]:%d", host, port);
}

enum fwdkind { FWD_DYNAMIC, FWD_LOCAL, FWD_REMOTE };

static void
dump_forwards(enum fwdkind kind, const struct fwdlist *l)
{
	static const char *names[] = {
		"dynamicforward", "localforward", "remoteforward"
	};
	const struct forward *fwd;
	int i, socks;

	for (i = 0; i < l->n; i++) {
		fwd = &l->v[i];
		socks = fwd->connect_host != NULL &&
		    strcmp(fwd->connect_host, "socks") == 0;
		if (kind == FWD_DYNAMIC && fwd->connect_host != NULL && !socks)
			continue;
		if (kind == FWD_LOCAL && socks)
			continue;
		printf("%s", names[kind]);
		dump_endpoint(fwd->listen_host, fwd->listen_port,
		    fwd->listen_path);
		if (kind != FWD_DYNAMIC)
			dump_endpoint(fwd->connect_host, fwd->connect_port,
			    fwd->connect_path);
		printf("\n");
	}
}

/* Print the resolved configuration, in the order ssh -G uses. */
void
dump_client_config(const Options *o, const char *host)
{
	int numeric;

	dump_string("host", o->host_arg);
	dump_string("user", o->user);
	dump_string("hostname", host);
	printf("port %d\n", o->port);

	printf("batchmode %s\n", fmt_flag(o->batch_mode));
	printf("controlmaster %s\n", fmt_controlmaster(o->control_master));
	printf("identitiesonly %s\n", fmt_flag(o->identities_only));
	printf("stricthostkeychecking %s\n",
	    fmt_strict(o->strict_host_key_checking));

	printf("serveralivecountmax %d\n", o->server_alive_count_max);
	printf("serveraliveinterval %d\n", o->server_alive_interval);

	dump_string("controlpath", o->control_path);
	dump_string("hostkeyalias", o->host_key_alias);
	dump_string("remotecommand", o->remote_command);
	dump_string("loglevel", fmt_loglevel(o->log_level));

	dump_forwards(FWD_DYNAMIC, &o->local_forwards);
	dump_forwards(FWD_LOCAL, &o->local_forwards);
	dump_forwards(FWD_REMOTE, &o->remote_forwards);

	dump_strarray("identityfile", &o->identity_files);
	dump_strarray("certificatefile", &o->certificate_files);
	dump_strarray_oneline("userknownhostsfile", &o->user_hostfiles);
	dump_strarray("sendenv", &o->send_env);
	dump_strarray("setenv", &o->setenv);

	if (o->forward_agent_sock_path == NULL)
		printf("forwardagent %s\n", fmt_flag(o->forward_agent));
	else
		dump_string("forwardagent", o->forward_agent_sock_path);

	if (o->connection_timeout == -1)
		printf("connecttimeout none\n");
	else
		printf("connecttimeout %d\n", o->connection_timeout);

	if (o->control_persist == 0 || o->control_persist_timeout == 0)
		printf("controlpersist %s\n", fmt_flag(o->control_persist));
	else
		printf("controlpersist %d\n", o->control_persist_timeout);

	if (o->jump_host == NULL)
		dump_string("proxycommand", o->proxy_command);
	else {
		numeric = strchr(o->jump_host, ':') != NULL ||
		    strspn(o->jump_host, "1234567890.") == strlen(o->jump_host);
		printf("proxyjump %s%s%s%s%s%s%s",
		    o->jump_extra == NULL ? "" : o->jump_extra,
		    o->jump_extra == NULL ? "" : ",",
		    o->jump_user == NULL ? "" : o->jump_user,
		    o->jump_user == NULL ? "" : "@",
		    numeric ? "[" : "",
		    o->jump_host,
		    numeric ? "]" : "");
		if (o->jump_port > 0)
			printf(":%d", o->jump_port);
		printf("\n");
	}
}
