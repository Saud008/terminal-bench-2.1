# Environment marker evaluation

requires_python strings use python_version comparisons such as python_version>="3.10". Compare python_version tuples numerically by major and minor, not as plain strings.

sys_platform and platform_machine markers compare exact string equality against the scenario target platform and architecture.
