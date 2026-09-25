---
name: documentation-links
description: Check documentation links and verify their local file and section targets.
---

# Documentation Links

Review links in the selected repository documentation and identify links that do not resolve to their intended target. Correct a broken link when the intended target is clear from the repository. If it is unclear, leave it unchanged and report the ambiguity.

Run `scripts/check_links.py` from this skill's directory with the currently active Python executable and pass the repository root with `--root`. For example: `python <skill-directory>/scripts/check_links.py --root <repository-root>`. It checks local target files and section fragments, resolving relative paths from the document containing the link. External URLs are skipped.

If no project checker is available, inspect the Markdown links in scope and verify their local paths and section fragments using available tools. Check link forms not covered by the project's checker separately. External URLs need not be checked unless the project procedure requires it and network access is available; report when they were not checked.

Report link corrections to the parent skill, including the source document and destination. The parent skill owns the final validation pass. Do not copy surrounding document content into the report.
