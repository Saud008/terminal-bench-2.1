package pqcli

import "github.com/terminus/pqgov/internal/auditexport"

func ExportAuditTenant(tenantID, scenario, output string) error {
	return auditexport.ExportAudit(tenantID, scenario, output)
}
