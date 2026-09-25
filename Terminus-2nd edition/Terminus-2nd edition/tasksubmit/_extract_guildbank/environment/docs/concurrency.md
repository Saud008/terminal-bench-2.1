# Gold withdraw concurrency

Concurrent POST /v1/guild/{guildId}/withdraw/gold requests must not drive guilds.gold_balance negative.

Gold withdraw paths must serialize balance checks and updates under a SQLite write transaction with immediate locking before reading gold_balance.

Reject with 409 when the post-withdraw balance would be negative. Successful concurrent bursts must leave a balance equal to initial_gold minus the sum of successful withdraw amounts.
