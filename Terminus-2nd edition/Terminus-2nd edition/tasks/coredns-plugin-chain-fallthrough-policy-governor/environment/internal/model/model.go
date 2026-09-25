package model

import "github.com/miekg/dns"

type RewriteRule struct {
	Mode     string // suffix | exact
	From     string
	To       string
	Continue bool
}

type ServerBlock struct {
	Zone        string
	Fallthrough bool
	PluginNames []string
	Rewrite     *RewriteRule
	CacheTTL    int
	HostsPath   string
}

type Corefile struct {
	Blocks []ServerBlock
}

type QueryCtx struct {
	Zone      string
	Qname     string
	Qtype     uint16
	ClientIP  string
	Fallthrough bool
	Rew       dns.ResponseWriter
	Req       *dns.Msg
	Msg       *dns.Msg
	Handled   bool
	StopChain bool
}
