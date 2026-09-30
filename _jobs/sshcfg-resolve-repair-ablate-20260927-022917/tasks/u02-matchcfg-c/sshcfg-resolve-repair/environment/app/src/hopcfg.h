#ifndef HOPCFG_H
#define HOPCFG_H

#define _GNU_SOURCE
#include <stddef.h>
#include <pwd.h>

#define MAX_INCLUDE_DEPTH	16
#define MAX_HOSTFILES		16
#define MAX_IDENTITY_FILES	100
#define MAX_CERTIFICATE_FILES	100
#define DEFAULT_SSH_PORT	22

/* readconf flags */
#define CONF_USER		0x01
#define CONF_NEVERMATCH		0x02
#define CONF_FINAL		0x04

/* StrictHostKeyChecking */
#define STRICT_OFF		0
#define STRICT_NEW		1
#define STRICT_YES		2
#define STRICT_ASK		3

/* ControlMaster */
#define CTL_NO			0
#define CTL_YES			1
#define CTL_ASK			2
#define CTL_AUTO		3
#define CTL_AUTO_ASK		4

/* LogLevel */
#define LOG_UNSET		-1
#define LOG_QUIET		0
#define LOG_FATAL		1
#define LOG_ERROR		2
#define LOG_INFO		3
#define LOG_VERBOSE		4
#define LOG_DEBUG1		5
#define LOG_DEBUG2		6
#define LOG_DEBUG3		7

#define PORT_STREAMLOCAL	-2

struct strlist {
	char **v;
	int n;
};

struct forward {
	char *listen_host;
	int listen_port;
	char *listen_path;
	char *connect_host;
	int connect_port;
	char *connect_path;
};

struct fwdlist {
	struct forward *v;
	int n;
};

typedef struct {
	char *host_arg;
	char *user;
	char *hostname;
	char *host_key_alias;
	char *proxy_command;
	char *control_path;
	char *remote_command;
	char *ignored_unknown;
	char *forward_agent_sock_path;

	char *jump_user;
	char *jump_host;
	char *jump_extra;
	int jump_port;

	int port;
	int batch_mode;
	int control_master;
	int identities_only;
	int strict_host_key_checking;
	int server_alive_count_max;
	int server_alive_interval;
	int log_level;
	int forward_agent;
	int connection_timeout;
	int control_persist;
	int control_persist_timeout;
	int clear_forwardings;

	struct strlist identity_files;
	struct strlist certificate_files;
	struct strlist user_hostfiles;
	struct strlist send_env;
	struct strlist setenv;

	struct fwdlist local_forwards;
	struct fwdlist remote_forwards;
} Options;

/* the passwd entry of the invoking user */
extern struct passwd *hop_pw;

/* xmalloc.c */
void *xmalloc(size_t);
void *xcalloc(size_t, size_t);
void *xreallocarray(void *, size_t, size_t);
char *xstrdup(const char *);
char *xstrndup(const char *, size_t);
int xasprintf(char **, const char *, ...)
    __attribute__((format(printf, 2, 3)));

/* log.c */
void error(const char *, ...) __attribute__((format(printf, 1, 2)));
void fatal(const char *, ...) __attribute__((format(printf, 1, 2), noreturn));

/* strlist.c */
void strlist_append(struct strlist *, const char *);
int strlist_contains(const struct strlist *, const char *);
void strlist_remove_matching(struct strlist *, const char *);
void strlist_clear(struct strlist *);

/* tokens.c */
char *strdelim(char **);
int argv_split(const char *, int *, char ***, int);
char *argv_next(int *, char ***);
void argv_consume(int *);
void argv_free(char **, int);
void lowercase(char *);
void rtrim(char *);

/* match.c */
int match_pattern(const char *, const char *);
int match_pattern_list(const char *, const char *, int);
int match_hostname(const char *, const char *);

/* convtime.c */
int convtime(const char *);
int a2port(const char *);
const char *atoi_err(const char *, int *);

/* expand.c */
struct expand_key {
	char key;
	const char *value;
};
char *percent_expand(const char *, const struct expand_key *);
char *percent_dollar_expand(const char *, const struct expand_key *);
char *dollar_expand(int *, const char *);
char *tilde_expand_filename(const char *);
int valid_env_name(const char *);

/* hostspec.c */
char *hpdelim(char **);
char *hpdelim2(char **, char *);
char *cleanhostname(char *);
int parse_user_host_port(const char *, char **, char **, int *);
int parse_ssh_uri(const char *, char **, char **, int *);
int valid_domain(char *, int);
int valid_hostname(const char *);
int valid_ruser(const char *);
int is_addr(const char *);
int canonical_addr(const char *, char *, size_t);

/* forward.c */
int parse_forward(struct forward *, const char *, int, int);
void add_forward(struct fwdlist *, const struct forward *);
void free_forward(struct forward *);
void clear_forwards(struct fwdlist *);

/* jump.c */
int parse_jump(const char *, Options *, int);

/* keywords.c */
enum opcode {
	oBadOption,
	oHost, oMatch, oInclude, oIgnoreUnknown,
	oUser, oHostname, oPort, oBatchMode, oControlMaster,
	oIdentitiesOnly, oStrictHostKeyChecking, oServerAliveCountMax,
	oServerAliveInterval, oControlPath, oHostKeyAlias, oRemoteCommand,
	oLogLevel, oDynamicForward, oLocalForward, oRemoteForward,
	oIdentityFile, oCertificateFile, oUserKnownHostsFile, oSendEnv,
	oSetEnv, oForwardAgent, oConnectTimeout, oControlPersist,
	oProxyCommand, oProxyJump, oClearAllForwardings,
	oCanonicalizeHostname,
	oPassthrough, oIgnore, oDeprecated, oUnsupported,
	oIgnoredUnknownOption
};
enum opcode lookup_keyword(const char *, const char *);

/* matchcfg.c */
int match_cfg_line(Options *, char **, const char *, const char *, int,
    int *, const char *, int);

/* readconf.c */
int process_config_line(Options *, const char *, const char *, char *,
    const char *, int, int *, int, int *, int);
int read_config_file(const char *, const char *, const char *, Options *,
    int, int *);

/* options.c */
void initialize_options(Options *);
void fill_default_options(Options *);

/* dump.c */
void dump_client_config(const Options *, const char *);

#endif
