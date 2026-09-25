# QA checks for src_install

QA hooks run twice during src_install: qa_preflight after normalize_d, and qa_postflight after dosbin. Preflight runs directory normalization and symlink containment checks only. Postflight repeats those checks and also enforces setuid preservation after fperms and dosbin have run. Preflight must not require setuid bits that fperms has not applied yet.

## qa_check_normalized_dirs

Every directory under D must be mode 0755. Failure aborts the phase with a non-zero exit status.

## qa_check_symlinks_contained

For each symbolic link under D, the resolved target must remain under D. Links whose resolved target is outside D fail QA.

## qa_check_setuid_preserved

For each fperms line whose mode begins with 4 (setuid), the installed file under D must still have the user setuid bit after fperms and dosbin complete. Postflight enforces this after dosbin runs.

## Trace contract

Each QA invocation records qa_preflight or qa_postflight in /app/state/phase-trace.json; normalize_d must appear before the first qa_preflight entry.
