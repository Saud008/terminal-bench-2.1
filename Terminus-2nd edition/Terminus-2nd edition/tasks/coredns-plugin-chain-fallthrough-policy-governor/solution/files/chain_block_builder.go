package chain

import (
	"github.com/terminus/dnsplugd/internal/model"
	"github.com/terminus/dnsplugd/internal/plugin"
	"github.com/terminus/dnsplugd/internal/plugins"
)

func Build(block model.ServerBlock) []plugin.Plugin {
	names := append([]string(nil), block.PluginNames...)
	var out []plugin.Plugin
	for _, n := range names {
		switch n {
		case "rewrite":
			if block.Rewrite != nil {
				out = append(out, plugins.NewRewrite(*block.Rewrite))
			}
		case "whoami":
			out = append(out, plugins.NewWhoami())
		case "cache":
			out = append(out, plugins.NewCache(block.CacheTTL))
		case "hosts":
			out = append(out, plugins.NewHosts(block.HostsPath))
		}
	}
	return out
}
