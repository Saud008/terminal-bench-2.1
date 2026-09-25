# seq atomicity

/app/var/spool/at/.SEQ holds the next sequence integer as decimal text plus newline.

Updates must write a temporary file in the same directory and rename into place so a crash cannot leave a partial .SEQ body.
