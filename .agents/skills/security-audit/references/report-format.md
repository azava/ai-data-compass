# Report format

Reports are metadata-only. They must never contain matching lines, snippets, values, partial values, reversible fingerprints, or raw scanner errors.

Each finding contains:

- `source`: `working-tree` or `git-history`;
- `file`: repository-relative path;
- `line`: line number, or `0` for filename findings;
- `rule_id`;
- `category`;
- `severity`;
- `confidence`;
- `commit`: present for history findings.

The report also records the scan mode, current commit, file count, finding count, truncation status, and generic scan warnings.
