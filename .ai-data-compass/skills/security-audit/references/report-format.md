# Report format

Canonical report-format reference for the AI Data Compass security-audit skill.

Reports are metadata-only. They must never contain matching lines, snippets, values, partial values, reversible fingerprints, or raw scanner errors.

Each finding contains:

- `source`: `working-tree`, `filesystem`, or `git-history`;
- `file`: repository-relative path;
- `line`: line number, or `0` for filename findings;
- `rule_id`;
- `category`;
- `severity`;
- `confidence`;
- `commit`: present for history findings.

The report also records the scan mode, completion status, file count, finding count, truncation status, and generic scan warnings. Filesystem reports set `commit` to `null`; the history mode is unavailable outside Git. Filesystem mode includes ignored files under the selected root, prunes `.git` entries, and does not follow symlinks. Enumeration or read failures set `complete` to `false` and return exit code `2`.
