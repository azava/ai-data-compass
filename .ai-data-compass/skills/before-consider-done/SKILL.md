---
name: before-consider-done
description: Run the repository's validation procedure before considering a task done.
---

# Before Consider Done

Use the task-completion procedure configured for the current project first. This skill does not replace project-specific procedures or expand the task scope. Perform the applicable checks and report evidence, unavailable capabilities, and unresolved issues.

## Before Considering a Task Done

Use the task-completion procedure configured for the current project first. The rules below are fallback guidance and should not contradict it. Project-specific procedures take precedence over AI Data Compass defaults. If no local procedure exists, use `.ai-data-compass/docs/task-completion.md`. If a required capability is unavailable, report it and require review rather than silently skipping it.

- Run all applicable repository tests, assertions, validations, and similar checks.
- Run the quality and metadata metrics selected for the project. AI code editors must compare the metrics after their changes with the last stable metrics for the environment and justify every change. They must treat the metrics as a feedback cycle for the AI agent, not as informational output only. Each metric should improve or remain stable. If no metrics are configured, explicitly inform the user.
- Verify that assertions, tests, and validations are updated and accurate.
- Review documentation across the repository, including READMEs, instructions, templates, backlog, and integration docs. Use the configured documentation-validation procedure; if none exists, look for the skill under `.ai-data-compass/skills/`.
  - Treat local-link validation and content-accuracy review as separate required checks. A successful link check does not establish that documentation claims are accurate.
  - For accuracy, compare substantive claims with relevant source code, configuration, command help, tests, and workflows. Correct clear inaccuracies and verify corrections against that evidence.
  - Report the scope and evidence for each check separately. If either check is unavailable or inconclusive, state the limitation and require review rather than implying it passed.
  - Follow the documentation-validation procedure's final validation and report unresolved issues. If neither the procedure nor skill is available, tell the user and require review.
- Review repository files and relevant Git history for accidental credentials, sensitive data, PII, or PHI without exposing matched values. Use the configured security audit procedure. If no local procedure exists, use `.ai-data-compass/docs/security-and-privacy.md`. If neither exists, explicitly inform the user that no security procedure is configured or installed, and require review.

For more details, see [Task Completion](../../docs/task-completion.md).
