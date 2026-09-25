# Gold withdraw concurrency

Concurrent `POST /v1/guild/{guildId}/withdraw/gold` requests share one treasury balance. Overdraw attempts must not leave `guilds.gold_balance` negative; those requests return **409** and leave the balance unchanged. Successful withdraws decrement the durable balance by their amounts.
