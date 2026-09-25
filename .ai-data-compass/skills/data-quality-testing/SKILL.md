---
name: data-quality-testing
description: Plan tests for data quality and business rules.
---

# Data Quality Testing

Help the user design, implement, and evaluate tests for data quality and business rules with the project's native data and test tools. Keep the work focused on testable data behavior rather than application-code tests, repository quality metrics, metadata management, or ongoing observability.

## Privacy and data-access boundaries

These safeguards apply before, during, and after every step, whether or not repository agent instructions are installed:

- Never expose, copy, export, or intentionally access sensitive data or personally identifiable information (PII) values. Treat credentials, tokens, secrets, private keys, personal records, and identifying information as sensitive.
- Inspect schemas, metadata, table definitions, column names, row counts, aggregates, and other non-value metadata only when needed. Inspect dataset contents only when the operation can be performed without accessing sensitive or PII values.
- Do not select, display, export, reconstruct, derive, or attempt to identify sensitive or PII values from other data. Do not run a test query or job that reads protected values, even if its output would only show aggregates.
- If a field or dataset's sensitivity is uncertain, do not access its values. Consult the configured security documentation or ask the user to identify the applicable procedure.
- For validation, prefer schemas, aggregates, row counts, safe comparisons, sanitized or synthetic fixtures, and structurally representative data over inspecting individual records.
- Keep sensitive values out of fixtures, query output, logs, reports, and coverage records. Report only safe metadata and aggregate results; do not include failing row examples.

## Establish scope and discover the data stack

- Confirm or infer whether the user wants the whole repository, selected changes, specific pipelines, datasets, batches, or business rules. State the scope; ask when ambiguity would materially change the work.
- Inspect project instructions, data documentation, existing quality rules, and current tests without reading protected values.
- Identify relevant languages, data frameworks, storage and compute systems, test tools, execution commands, and existing environments. Use the project's native capabilities, such as dbt tests, SQL assertions, pandas or PySpark suites, Flink tests, or Dataflow tests, when they fit the project.
- Identify applicable rules such as required fields, types, formats, ranges, allowed values, referential integrity, completeness, uniqueness, duplicates, cross-dataset consistency, and deterministic business assertions.
- Distinguish data-quality tests from code-behavior tests, metadata/catalog completeness, repository quality metrics, and continuous monitoring.

## Assess infrastructure and execution with the user

Discuss where each test can and should run before starting execution. The agent may not have access to the required data platform or environment; the user may run the test elsewhere and return a safe report.

For each candidate execution mode, assess and discuss:

- The data source, volume, partitions, expected scan size, and whether the rule is local, batch-wide, or global.
- The required platform, compute, storage, permissions, dependencies, network access, and any shuffle or cross-system transfer.
- The expected runtime and cost, with assumptions. Use qualitative estimates or ranges when exact costs are unavailable; do not invent precision.
- The environment and execution owner: local synthetic setup, CI, staging, an authorized cluster or managed service, or a production-like environment.
- Privacy controls, read-only guarantees, and any operational side effects.

Choose among local, synthetic, sampled, partitioned, cluster, and full-scale execution based on the rule's correctness needs and the project's constraints. Do not impose a blanket preference for small or local tests: some rules require distributed execution or representative infrastructure. A sample or partition check cannot establish a global property such as whole-dataset uniqueness unless the test design proves that it can.

Do not start expensive execution, create billable infrastructure, or run production-like jobs without the user's explicit agreement. If the agent lacks access, prepare reproducible commands or job instructions, state prerequisites and expected safe outputs, and let the user run them. Never request credentials in chat or store them in test artifacts.

## Map existing checks and recommend a starting point

- Review existing quality tests, assertions, business rules, and documentation for the selected scope. Classify each rule as absent, partially covered, covered, or not verifiable, and cite the evidence and confidence.
- Distinguish a true test gap from a rule that is intentionally out of scope, unsafe to evaluate with available data, or dependent on unavailable infrastructure.
- Treat test counts or numeric coverage as supporting evidence only. Assess whether checks validate the intended rule, meaningful boundaries, failure behavior, and the required data scope.

Present a concise map, then recommend three useful starting areas tailored to the findings. For each, state the rule or behavior, the proposed test approach, data scope, privacy constraints, execution environment, and estimated cost or uncertainty. Let the user choose one or name another area.

## Work through one testing round

For the selected area:

- Propose concrete assertions and scenarios using the project's conventions and native tools.
- Agree with the user on the rule, data scope, fixture or safe metadata strategy, execution mode, environment owner, expected cost, and privacy controls before running it.
- Implement only the agreed tests. Keep fixtures synthetic or sanitized, make assertions deterministic where practical, and avoid changing source data.
- If a test requires protected values or cannot satisfy the privacy rules, do not run it; explain the limitation and suggest a safe alternative or require the project's authorized review process.
- If a test exposes a data or business-rule failure, report safe aggregate evidence. Do not modify production data, pipeline behavior, or business rules unless the user explicitly included those changes in scope.
- Report exact commands or job instructions and distinguish passed, failed, skipped, user-run, and unavailable checks. Include actual runtime or cost only when it was measured; otherwise label estimates and assumptions.

When the agent cannot execute a test, give the user the reproducible steps and the expected redacted or aggregate result format. Review the returned result without asking for raw records or sensitive examples.

## Record the reviewed coverage

When the user accepts a round as complete, check whether the repository already maintains a record of data-quality coverage or known gaps.

- If a suitable record exists, update it only when documentation changes are authorized and the new state warrants an update.
- If no suitable record exists, suggest a concise Markdown record in the project's documentation location, such as `docs/data-quality-coverage.md`, and ask before creating it.
- Record the review date or revision, scope, rules assessed, safe test evidence, execution environment, who ran the check, volume or partition scope, measured or estimated cost, privacy controls, remaining gaps, and limitations. Never record sensitive values or raw row examples.
- On later runs, use the record to guide discovery, but recheck current rules, tests, data scope, privacy classification, infrastructure, and costs. Do not treat the record as authoritative or current.

## Continue or finish

- After each completed round, ask whether the user wants another round, on the same or a different area.
- Keep each round focused and repeat the privacy, execution, and cost assessment when its scope or environment changes.
- When the user decides to stop, summarize rules reviewed and tests added or run, safe results, execution owner and environment, measured or estimated cost, remaining gaps, and unavailable checks. Do not continue without the user's choice.
