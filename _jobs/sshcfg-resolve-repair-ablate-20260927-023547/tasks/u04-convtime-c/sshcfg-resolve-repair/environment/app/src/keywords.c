#include "hopcfg.h"

#include <string.h>

/*
 * Every keyword understood by the Debian bookworm ssh client.  Keywords
 * that do not influence any value hopcfg prints are accepted and skipped
 * (oPassthrough).
 */
static const struct {
	const char *name;
	enum opcode opcode;
} keywords[] = {
	{ "protocol", oIgnore },
	{ "cipher", oDeprecated },
	{ "fallbacktorsh", oDeprecated },
	{ "globalknownhostsfile2", oDeprecated },
	{ "rhostsauthentication", oDeprecated },
	{ "useblacklistedkeys", oDeprecated },
	{ "userknownhostsfile2", oDeprecated },
	{ "useroaming", oDeprecated },
	{ "usersh", oDeprecated },
	{ "useprivilegedport", oDeprecated },

	{ "afstokenpassing", oUnsupported },
	{ "kerberosauthentication", oUnsupported },
	{ "kerberostgtpassing", oUnsupported },
	{ "rsaauthentication", oUnsupported },
	{ "rhostsrsaauthentication", oUnsupported },
	{ "compressionlevel", oUnsupported },

	{ "gssapiauthentication", oPassthrough },
	{ "gssapikeyexchange", oPassthrough },
	{ "gssapidelegatecredentials", oPassthrough },
	{ "gssapitrustdns", oPassthrough },
	{ "gssapiclientidentity", oPassthrough },
	{ "gssapiserveridentity", oPassthrough },
	{ "gssapirenewalforcesrekey", oPassthrough },
	{ "gssapikexalgorithms", oPassthrough },
	{ "pkcs11provider", oPassthrough },
	{ "smartcarddevice", oPassthrough },

	{ "forwardagent", oForwardAgent },
	{ "forwardx11", oPassthrough },
	{ "forwardx11trusted", oPassthrough },
	{ "forwardx11timeout", oPassthrough },
	{ "exitonforwardfailure", oPassthrough },
	{ "xauthlocation", oPassthrough },
	{ "gatewayports", oPassthrough },
	{ "passwordauthentication", oPassthrough },
	{ "kbdinteractiveauthentication", oPassthrough },
	{ "kbdinteractivedevices", oPassthrough },
	{ "challengeresponseauthentication", oPassthrough },
	{ "skeyauthentication", oPassthrough },
	{ "tisauthentication", oPassthrough },
	{ "pubkeyauthentication", oPassthrough },
	{ "dsaauthentication", oPassthrough },
	{ "hostbasedauthentication", oPassthrough },
	{ "identityfile", oIdentityFile },
	{ "identityfile2", oIdentityFile },
	{ "identitiesonly", oIdentitiesOnly },
	{ "certificatefile", oCertificateFile },
	{ "addkeystoagent", oPassthrough },
	{ "identityagent", oPassthrough },
	{ "hostname", oHostname },
	{ "hostkeyalias", oHostKeyAlias },
	{ "proxycommand", oProxyCommand },
	{ "port", oPort },
	{ "ciphers", oPassthrough },
	{ "macs", oPassthrough },
	{ "remoteforward", oRemoteForward },
	{ "localforward", oLocalForward },
	{ "permitremoteopen", oPassthrough },
	{ "user", oUser },
	{ "host", oHost },
	{ "match", oMatch },
	{ "escapechar", oPassthrough },
	{ "globalknownhostsfile", oPassthrough },
	{ "userknownhostsfile", oUserKnownHostsFile },
	{ "connectionattempts", oPassthrough },
	{ "batchmode", oBatchMode },
	{ "checkhostip", oPassthrough },
	{ "stricthostkeychecking", oStrictHostKeyChecking },
	{ "compression", oPassthrough },
	{ "tcpkeepalive", oPassthrough },
	{ "keepalive", oPassthrough },
	{ "numberofpasswordprompts", oPassthrough },
	{ "syslogfacility", oPassthrough },
	{ "loglevel", oLogLevel },
	{ "logverbose", oPassthrough },
	{ "dynamicforward", oDynamicForward },
	{ "preferredauthentications", oPassthrough },
	{ "hostkeyalgorithms", oPassthrough },
	{ "casignaturealgorithms", oPassthrough },
	{ "bindaddress", oPassthrough },
	{ "bindinterface", oPassthrough },
	{ "clearallforwardings", oClearAllForwardings },
	{ "enablesshkeysign", oPassthrough },
	{ "verifyhostkeydns", oPassthrough },
	{ "nohostauthenticationforlocalhost", oPassthrough },
	{ "rekeylimit", oPassthrough },
	{ "connecttimeout", oConnectTimeout },
	{ "addressfamily", oPassthrough },
	{ "serveraliveinterval", oServerAliveInterval },
	{ "serveralivecountmax", oServerAliveCountMax },
	{ "sendenv", oSendEnv },
	{ "setenv", oSetEnv },
	{ "controlpath", oControlPath },
	{ "controlmaster", oControlMaster },
	{ "controlpersist", oControlPersist },
	{ "hashknownhosts", oPassthrough },
	{ "include", oInclude },
	{ "tunnel", oPassthrough },
	{ "tunneldevice", oPassthrough },
	{ "localcommand", oPassthrough },
	{ "permitlocalcommand", oPassthrough },
	{ "remotecommand", oRemoteCommand },
	{ "visualhostkey", oPassthrough },
	{ "kexalgorithms", oPassthrough },
	{ "ipqos", oPassthrough },
	{ "requesttty", oPassthrough },
	{ "sessiontype", oPassthrough },
	{ "stdinnull", oPassthrough },
	{ "forkafterauthentication", oPassthrough },
	{ "proxyusefdpass", oPassthrough },
	{ "canonicaldomains", oPassthrough },
	{ "canonicalizefallbacklocal", oPassthrough },
	{ "canonicalizehostname", oCanonicalizeHostname },
	{ "canonicalizemaxdots", oPassthrough },
	{ "canonicalizepermittedcnames", oPassthrough },
	{ "streamlocalbindmask", oPassthrough },
	{ "streamlocalbindunlink", oPassthrough },
	{ "revokedhostkeys", oPassthrough },
	{ "fingerprinthash", oPassthrough },
	{ "updatehostkeys", oPassthrough },
	{ "hostbasedacceptedalgorithms", oPassthrough },
	{ "hostbasedkeytypes", oPassthrough },
	{ "pubkeyacceptedalgorithms", oPassthrough },
	{ "pubkeyacceptedkeytypes", oPassthrough },
	{ "ignoreunknown", oIgnoreUnknown },
	{ "proxyjump", oProxyJump },
	{ "securitykeyprovider", oPassthrough },
	{ "knownhostscommand", oPassthrough },
	{ "requiredrsasize", oPassthrough },
	{ "enableescapecommandline", oPassthrough },
	{ "protocolkeepalives", oServerAliveInterval },
	{ "setuptimeout", oServerAliveInterval },
	{ NULL, oBadOption }
};

/* keyword must already be lowercase */
enum opcode
lookup_keyword(const char *keyword, const char *ignored_unknown)
{
	int i;

	for (i = 0; keywords[i].name != NULL; i++)
		if (strcmp(keyword, keywords[i].name) == 0)
			return keywords[i].opcode;
	if (ignored_unknown != NULL &&
	    match_pattern_list(keyword, ignored_unknown, 1) == 1)
		return oIgnoredUnknownOption;
	return oBadOption;
}
