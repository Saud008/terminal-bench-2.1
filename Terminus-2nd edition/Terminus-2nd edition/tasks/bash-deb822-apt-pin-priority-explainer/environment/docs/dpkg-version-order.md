# Dpkg version order

Dpkg ordering compares version epoch field, upstream version, then debian revision. Tilde segments sort before the same segment without tilde. When effective priorities tie, the newer version wins.
