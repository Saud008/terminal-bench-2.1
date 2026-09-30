#include "hopcfg.h"

#include <stdlib.h>
#include <string.h>
#include <strings.h>

static const char *default_identities[] = {
	"~/.ssh/id_rsa",
	"~/.ssh/id_ecdsa",
	"~/.ssh/id_ecdsa_sk",
	"~/.ssh/id_ed25519",
	"~/.ssh/id_ed25519_sk",
	"~/.ssh/id_xmss",
	"~/.ssh/id_dsa",
	NULL
};

void
initialize_options(Options *o)
{
	memset(o, 0, sizeof(*o));
	o->jump_port = -1;
	o->port = -1;
	o->batch_mode = -1;
	o->control_master = -1;
	o->identities_only = -1;
	o->strict_host_key_checking = -1;
	o->server_alive_count_max = -1;
	o->server_alive_interval = -1;
	o->log_level = LOG_UNSET;
	o->forward_agent = -1;
	o->connection_timeout = -1;
	o->control_persist = -1;
	o->control_persist_timeout = 0;
	o->clear_forwardings = -1;
}

static void
clear_on_none(char **v)
{
	if (*v != NULL && strcasecmp(*v, "none") == 0) {
		free(*v);
		*v = NULL;
	}
}

/* Fill in defaults for everything the configuration left unset. */
void
fill_default_options(Options *o)
{
	int i;

	if (o->forward_agent == -1)
		o->forward_agent = 0;
	if (o->clear_forwardings == -1)
		o->clear_forwardings = 0;
	if (o->clear_forwardings == 1) {
		clear_forwards(&o->local_forwards);
		clear_forwards(&o->remote_forwards);
	}
	if (o->batch_mode == -1)
		o->batch_mode = 0;
	if (o->strict_host_key_checking == -1)
		o->strict_host_key_checking = STRICT_ASK;
	if (o->port == -1)
		o->port = 0;
	if (o->identity_files.n == 0)
		for (i = 0; default_identities[i] != NULL; i++)
			strlist_append(&o->identity_files, default_identities[i]);
	if (o->user_hostfiles.n == 0) {
		strlist_append(&o->user_hostfiles, "~/.ssh/known_hosts");
		strlist_append(&o->user_hostfiles, "~/.ssh/known_hosts2");
	}
	if (o->log_level == LOG_UNSET)
		o->log_level = LOG_INFO;
	if (o->identities_only == -1)
		o->identities_only = 0;
	if (o->server_alive_interval == -1)
		o->server_alive_interval = o->batch_mode == 1 ? 300 : 0;
	if (o->server_alive_count_max == -1)
		o->server_alive_count_max = 3;
	if (o->control_master == -1)
		o->control_master = CTL_NO;
	if (o->control_persist == -1) {
		o->control_persist = 0;
		o->control_persist_timeout = 0;
	}

	clear_on_none(&o->remote_command);
	clear_on_none(&o->proxy_command);
	clear_on_none(&o->control_path);
	if (o->jump_host != NULL && strcmp(o->jump_host, "none") == 0 &&
	    o->jump_port == 0 && o->jump_user == NULL) {
		free(o->jump_host);
		o->jump_host = NULL;
	}
}
