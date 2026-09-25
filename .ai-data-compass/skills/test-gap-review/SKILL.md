---
name: test-gap-review
description: Find missing behavior and regression tests in a repository or selected changes.
---

# Test Gap Review

Identify meaningful gaps in automated tests for code behavior, then work with the user to add tests for one chosen area at a time. Use the repository's own test frameworks, conventions, and execution commands.

This skill covers unit, integration, end-to-end, contract, and other code-behavior tests. It does not assess data quality, repository quality metrics, metadata, or infrastructure as independent targets.

## Establish scope and testing context

- Confirm or infer the requested scope: whole repository, current changes, branch comparison, or selected files. Ask a concise question if ambiguity would materially change the review; otherwise state the scope you will use.
- Inspect project instructions and relevant documentation.
- Identify languages, frameworks, build tools, test frameworks, and native test commands in scope. Follow documented project commands instead of assuming a generic runner.
- If tests or a runnable environment are unavailable, explain the limitation and continue with a static, evidence-based map.

## Map behavioral coverage

- Review relevant code, existing tests, test configuration, and documented bugs or known limitations.
- For each meaningful behavior or bug scenario, assess whether tests are absent, partial, or adequate. Consider expected behavior, important boundaries, failures, and documented regressions.
- Treat line or branch coverage as supporting evidence; percentages alone do not establish meaningful behavioral coverage.
- Use confidence labels when evidence is incomplete, and distinguish hard-to-exercise behavior from a genuine test gap.
- Respect project privacy rules. Do not inspect sensitive data values; use synthetic or sanitized fixtures.
- Keep the scope on code behavior. Do not expand into data validation, quality metrics, metadata, deployment, or infrastructure checks.

Present a concise map with evidence, then recommend three useful starting areas tailored to the findings. For example, suggest high-impact behavior with partial coverage, a documented bug without a regression test, or behavior affected by selected changes. Briefly explain each suggestion and let the user choose one or name another area.

## Work through one round

For the selected area:

- Propose concrete test scenarios and appropriate test levels using project conventions.
- Discuss the proposal with the user and adjust it until the target behavior is clear.
- Implement only the agreed tests, following existing patterns and native tools.
- Do not change production behavior just because a test exposes a bug. Report the evidence and ask how the user wants to proceed unless the requested scope already authorizes the fix.
- Run relevant native tests when the user requested implementation or execution and the environment permits it.
- Report exact commands and outcomes; distinguish passed, failed, skipped, and unavailable checks. Do not claim unverified coverage, and separate unrelated failures from this round.

## Record the reviewed coverage

When the user accepts a round as complete, check whether the repository already maintains a record of test coverage or known test gaps.

- If a suitable record exists, update it only when the user authorized documentation changes and the new state warrants an update.
- If no suitable record exists, suggest a concise Markdown record in the project's documentation location and ask before creating it.
- Record the review date or revision, scope, behaviors assessed, test evidence, remaining gaps, and deferred work. Percentages alone are insufficient.
- On later runs, use the record to guide discovery, but repeat the current inspection of technologies, code, tests, and documented bugs. Do not treat the record as authoritative or current.

## Continue or finish

- After each completed round, ask whether the user wants another. It may address a different area or continue the same area with different behavior or test levels.
- Repeat the mapping and agreement process for each round, keeping the work focused.
- When the user decides to stop, summarize reviewed and implemented areas, commands and results, remaining gaps, and limitations or follow-up decisions. Do not continue without the user's choice.
