# Severity precedence contract

policy.json severity_ranks maps labels to numeric ranks where lower numbers are more urgent. IMMEDIATE is most urgent. Seal bundle rank sort uses descending urgency by numeric rank then ascending zone_id. Lexical string rank sort of severity labels is incorrect.
