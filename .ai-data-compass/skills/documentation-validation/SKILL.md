---
name: documentation-validation
description: Check repository documentation links and accuracy against the current project.
---

# Documentation Validation

Use this skill to review and correct clear problems in repository documentation. By default review all repository documentation; use a narrower scope only when the user requests one. If the user explicitly requests a report without edits, follow that restriction.

Run both included reviews by reading and following [Documentation Links](subskills/documentation-links/SKILL.md) and [Documentation Accuracy](subskills/documentation-accuracy/SKILL.md). Do not skip either review. The subskills identify and correct clear documentation defects using repository evidence. After both reviews finish, perform one final validation pass for the changes: rerun the link checker once if documentation changed, and verify corrected accuracy claims against their evidence. Do not rerun the subskills or the full review. Do not change application code to make documentation claims appear accurate. If a finding is ambiguous or a check cannot be completed, report it as unresolved or unavailable rather than guessing or claiming it passed.

Summarize the scope, corrections made, validation results, and any unresolved findings with their document locations and recommended next steps. State explicitly when no issues were found. Keep results concise, actionable, and free of sensitive values.
