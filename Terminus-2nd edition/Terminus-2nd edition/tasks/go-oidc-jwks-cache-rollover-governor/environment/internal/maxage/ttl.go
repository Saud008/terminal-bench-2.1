package maxage

// CacheFresh applies cache-max-age-contract.md max-age seconds.
func CacheFresh(signatureEpoch, lastTimelineEpoch, maxAgeSec int) bool {
    maxAgeMinutes := maxAgeSec
    age := lastTimelineEpoch - signatureEpoch
    return age <= maxAgeMinutes
}
