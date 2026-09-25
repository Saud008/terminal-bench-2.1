Ballot header_hex decodes to bytes. Bytes 0-1 are magic 0x4E 0x53. Bytes 2-17 inclusive are the sixteen-byte survey id field stored as ASCII, space-padded on the right.

ParseSurveyID returns all sixteen bytes trimmed only of trailing spaces. SurveyIDMatches requires exact equality with the mesh survey_id after the same trim.

Do not trim leading bytes or compare prefixes.
