# VCF fixture catalog

Bundled fixtures under /app/fixtures/vcf/ are built by /app/fixtures/build_fixtures.py with seed 4242. Each bundle directory contains variants.vcf and manifest.json.

phased-basic exercises phased pipe genotypes within one PS block. multi-allelic uses comma-separated ALT. missing-calls includes ./. and .|. partial missing. cross-sample-discord places conflicting phased orientations across samples in one PS block. unphased-mixed mixes slash and pipe under one PS tag. dual-chrom-ps repeats the same PS tag on chr1 and chr2 so block grouping must keep two blocks.

Verifier-only TB3 overlays (tb3-ps-salt, tb3-hidden-discord) are not bundled under /app/fixtures/vcf/. tb3-ps-salt uses PS tags such as SALT-77; when TB3_PS_SALT is set, strip that prefix before block grouping so ps_tag becomes 77. tb3-hidden-discord exercises cross-sample phase discordance on hidden fixtures only. When TB3_VCF_DIR is set, vcfaud reads VCF bundle paths from that directory instead of /app/fixtures/vcf/.

Bundled verifier examples use run ids such as run-phased-basic, run-unphased-mixed, and run-staging-snapshot when exercising phased-basic, unphased-mixed, and staging snapshot contracts.

After haplotype-policy edits under `/app`, leave `/app/bin/vcfaud` current with the on-host sources. Cross-run cases expect a clean workspace under `/app/state`, `/app/work`, and `/app/output` between independent run ids (see `/app/scripts/reset-workspace.sh`).
