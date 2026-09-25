---
name: test-gap-review
description: Find and address gaps in behavior and regression tests.
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
- Examine assertions and expected outcomes, not just whether a test executes the code. Check whether mocks hide the behavior under review. Treat line or branch coverage as supporting evidence; percentages alone do not establish meaningful behavioral coverage.
- Use confidence labels when evidence is incomplete. Record test presence and execution status separately: an unavailable environment does not establish that tests are missing or inadequate.
- Respect project privacy rules. Do not inspect sensitive data values; use synthetic or sanitized fixtures.

Present a concise map with evidence, then recommend three useful starting areas tailored to the findings. For example, suggest high-impact behavior with partial coverage, a documented bug without a regression test, or behavior affected by selected changes. Briefly explain each suggestion and let the user choose one or name another area.

## Work through one round

For the selected area:

- Propose concrete test scenarios and appropriate test levels using project conventions. Include the coverage record in the round's scope.
- Discuss the proposal with the user and adjust it until the target behavior is clear.
- Implement only the agreed tests, following existing patterns and native tools.
- Do not change production behavior just because a test exposes a bug. Report the evidence and ask how the user wants to proceed unless the requested scope already authorizes the fix.
- Run relevant native tests when the user requested implementation or execution and the environment permits it. For a regression test with an available fix, verify when practical that it fails before the fix and passes after it, using an isolated setup that preserves the user's work. If that comparison cannot be performed, report the limitation.
- Report which tests already existed, which were added, and which were executed, with exact commands and outcomes. Distinguish passed, failed, skipped, and unavailable checks; do not describe unexecuted tests as passing. Separate unrelated failures from this round.

## Record the reviewed coverage

When the user accepts a round as complete, check whether the repository already maintains a record of test coverage or known test gaps.

- Update a suitable existing record or create a concise Markdown record in the project's documentation location when included in the authorized round. Do not request confirmation again for documentation work already authorized; propose it if it remains outside the agreed scope.
- Record the review date or revision, scope, behaviors assessed, existing and added tests, execution evidence and limitations, remaining gaps, and deferred work. Percentages alone are insufficient.
- On later runs, use the record to guide discovery, but repeat the current inspection of technologies, code, tests, and documented bugs. Do not treat the record as authoritative or current.

## Continue or finish

- After each completed round, ask whether the user wants another. It may address a different area or continue the same area with different behavior or test levels.
- Within the same execution, refresh the map for the selected area and effects of the changes, then agree on the next round. Repeat broader discovery only when scope changes or new evidence warrants it; on a new execution, recheck the current repository state.
- When the user decides to stop, summarize reviewed and implemented areas, commands and results, remaining gaps, and limitations or follow-up decisions. Do not continue without the user's choice.
