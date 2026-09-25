---
name: documentation-links
description: Check documentation links and verify their local file and section targets.
---

# Documentation Links

Review links in the selected repository documentation and identify links that do not resolve to their intended target. Correct a broken link when the intended target is clear from the repository. If it is unclear, leave it unchanged and report the ambiguity.

From the adopting repository root, run the checker bundled in the canonical `documentation-validation` skill directory: `python .ai-data-compass/skills/documentation-validation/scripts/check_links.py --root .`. If the skill directory has a collision suffix, use its installed name in that path. The checker tests local target files and section fragments, resolving relative paths from each document. It skips external URLs.

If no project checker is available, inspect the Markdown links in scope and verify their local paths and section fragments using available tools. Check link forms not covered by the project's checker separately. External URLs need not be checked unless the project procedure requires it and network access is available; report when they were not checked.

Report link corrections to the parent skill, including the source document and destination. The parent skill owns the final validation pass. Do not copy surrounding document content into the report.
