# Security Policy

## Reporting a vulnerability

Use [private vulnerability reporting](https://github.com/jbcom/extended-data/security/advisories/new) for security-sensitive reports. Do not open a public issue for an unpatched vulnerability.

Include affected versions, a minimal reproduction, impact, and any suggested mitigation. The project will acknowledge reports and coordinate disclosure through the advisory.

## Supported releases

Security fixes target the current release line. Deprecated package names and removed connector namespaces are intentionally unsupported.

## Supply-chain boundaries

External fork pull requests run without repository secrets, write tokens, publishing credentials, or Pages privileges. Trusted upstream branches must pass the repository policy, native CI, dependency review, CodeQL, and configured automated review before merge.
