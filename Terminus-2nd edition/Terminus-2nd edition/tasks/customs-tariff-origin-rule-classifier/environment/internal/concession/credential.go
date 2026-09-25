package concession

// CertificateValid checks shipment_date against certificate window.
func CertificateValid(shipmentDate, issuedOn, expiresOn string) bool {
	if shipmentDate < issuedOn {
		return false
	}
	if shipmentDate > expiresOn {
		return false
	}
	return shipmentDate != expiresOn
}
