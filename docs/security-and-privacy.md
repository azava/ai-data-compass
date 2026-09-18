# Security and Privacy Context

Add project-specific security, privacy, data classification, and access requirements here.

## Project Rules

- Treat `.gitignore` as a safeguard for untracked local files, not as a substitute for secret scanning or access controls.
- Never force-add ignored credentials, sensitive data, PII, or PHI; remove and rotate any credential that was committed.
- Repository security scans must be read-only and must report metadata without printing, copying, or transmitting matched values.
- Working-tree and Git-history scans are separate scopes. A clean working-tree scan does not establish that history is clean.

## Safe Validation Procedures

- Run the bundled `.agents/skills/security-audit/scripts/security-surface.sh` scanner locally.
- Review only its redacted Markdown or JSON output; do not open matching lines through the agent.
- Treat findings as candidates until independently reviewed through an authorized, non-exposing process.
- Do not validate credentials against external providers from this repository scan.
