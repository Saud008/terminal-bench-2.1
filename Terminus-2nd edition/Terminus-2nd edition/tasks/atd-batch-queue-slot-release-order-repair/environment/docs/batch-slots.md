# batch slots

Letters a through z name batch slots tracked under /app/var/spool/at/batch_slots/ as one marker file per held letter.

allocate_letter must scan from the scenario starting letter and advance while a spool job file already exists for the candidate letter or the batch slot marker is present. Retry until a free letter is found or allocation fails.
