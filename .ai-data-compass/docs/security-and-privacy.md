# Security and Privacy Details

This document contains additional security and privacy procedures for the rules in `AGENTS.md`.

## Project Rules

- Treat `.gitignore` as a safeguard for untracked local files, not as a substitute for secret scanning or access controls.
- Never force-add ignored credentials, sensitive data, PII, or PHI; remove and rotate any credential that was committed.
- Repository security scans should be read-only and should report metadata without printing, copying, or transmitting matched values.
- Working-tree, local filesystem, and Git-history scans are separate scopes. Use filesystem mode when the scan directory is not a valid Git repository; it includes ignored files below the selected root, prunes `.git` entries, and does not follow symlinks. A clean current-files scan does not establish that Git history is clean.

## Safe Validation Procedures

- Follow the security procedure configured for the repository. If the `security_audit` asset is installed, its bundled scanner is available at `.ai-data-compass/skills/security-audit/scripts/security-surface.sh`. If no scanner or procedure is available, report that limitation and require review.
- Review only its redacted Markdown or JSON output; do not open matching lines through the agent.
- Treat findings as candidates until independently reviewed through an authorized, non-exposing process.
- Do not validate credentials against external providers from the default repository scan.
