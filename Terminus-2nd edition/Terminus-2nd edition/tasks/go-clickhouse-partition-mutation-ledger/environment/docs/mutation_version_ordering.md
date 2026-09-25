# Mutation version ordering

When multiple mutation commands target the same partition_id, the effective mutation for readiness is the row with the **highest mutation_version** using **numeric** comparison.

String comparison is invalid. Version 10 must sort after version 9.
