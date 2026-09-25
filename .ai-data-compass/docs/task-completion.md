# Task Completion Details

Review the complete repository documentation surface before considering a task done, not only the files directly related to the change.

Include README files, agent instructions, backlog documents, templates, asset documentation, integration documentation, and operational procedures.

Validate internal Markdown links and repository path references against the current tree. Pay particular attention to references to moved, renamed, deleted, or generated files, assets, skills, adapters, workflows, and procedures.

Use the documentation-validation procedure configured for the current project. If no local procedure exists, look under `.ai-data-compass/skills/` for `documentation-validation` or a collision name formed with the `documentation-validation` prefix and `-ai-data-compass` suffix, optionally followed by a numeric suffix such as `-2`. Correct clear documentation issues found during the review and follow that procedure's final validation. Report issues that cannot be corrected confidently. If neither a local procedure nor the skill exists, inform the user that documentation validation could not be performed and require review.
