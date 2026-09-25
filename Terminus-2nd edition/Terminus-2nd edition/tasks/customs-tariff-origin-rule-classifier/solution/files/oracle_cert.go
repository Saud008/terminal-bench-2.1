package concession

func CertificateValid(shipmentDate, issuedOn, expiresOn string) bool {
	if shipmentDate < issuedOn {
		return false
	}
	if shipmentDate > expiresOn {
		return false
	}
	return true
}
