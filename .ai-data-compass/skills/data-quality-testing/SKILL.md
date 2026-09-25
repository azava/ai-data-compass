---
name: data-quality-testing
description: Design and implement tests for data quality and business rules.
---

# Data Quality Testing

Help the user design, implement, and evaluate tests for data quality and business rules with the project's native data and test tools. Keep the work focused on testable data behavior rather than application-code tests, repository quality metrics, metadata management, or ongoing observability.

## Privacy and data-access boundaries

These safeguards apply before, during, and after every step, whether or not repository agent instructions are installed:

- Never expose, copy, export, or intentionally access sensitive data or personally identifiable information (PII), or protected health information (PHI) values. Treat credentials, tokens, secrets, private keys, personal records, and identifying information as sensitive.
- PHI means Protected Health Information. Under HIPAA, it generally covers individually identifiable health information held or transmitted by covered entities or their business associates, subject to legal exclusions; see the [HHS guidance](https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html). For this workflow, treat identifiable health information as sensitive even when HIPAA applicability is unknown. Use project classifications and policies; do not inspect values to determine their classification.
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

## Map existing checks and recommend a starting point

- Review existing quality tests, assertions, business rules, and documentation for the selected scope. Classify each rule as absent, partially covered, covered, or not verifiable, and cite the evidence and confidence.
- Identify known privacy, access, or execution constraints that would rule out a suggestion. Distinguish test gaps from intentionally excluded or currently unverifiable rules.
- Treat test counts or numeric coverage as supporting evidence only. Assess whether checks validate the intended rule, meaningful boundaries, failure behavior, and the required data scope.

Present a concise map, then offer three useful starting areas and recommend one. Briefly explain the rule, expected benefit, and any known constraint that affects the choice. Let the user choose one or name another area; defer detailed execution planning to that round.

## Work through one testing round

For the selected area:

- Propose concrete assertions and scenarios using the project's conventions and native tools. Include the coverage record in the round's scope.
- Inspect available execution configuration and recommend a suitable approach. Discuss the recommendation with the user, asking only for missing information or consequential decisions about data scope, access, environment, and cost; reuse choices and authorization already established.
- For external, costly, large, distributed, sampled, or partitioned execution, read [Execution Planning](references/execution-planning.md). Evaluate only the considerations relevant to this round. A sample or partition cannot establish global properties such as whole-dataset uniqueness unless the design proves that it can.
- Do not start expensive execution, create billable infrastructure, or run production-like jobs without the user's explicit agreement. Never request credentials in chat or store them in test artifacts.
- Implement only the agreed tests. Keep fixtures synthetic or sanitized, make assertions deterministic where practical, and avoid changing source data.
- If a test requires protected values or cannot satisfy the privacy rules, do not run it; explain the limitation and suggest a safe alternative or require the project's authorized review process.
- If a test exposes a data or business-rule failure, report safe aggregate evidence. Do not modify production data, pipeline behavior, or business rules unless the user explicitly included those changes in scope.
- Report exact commands and distinguish passed, failed, skipped, user-run, and unavailable checks. Separate a test being implemented, its logic passing on synthetic fixtures, and the rule being evaluated on an authorized dataset in a named environment. Synthetic success does not establish that real data satisfies the rule.
- Include actual runtime or cost only when measured; otherwise label estimates and assumptions.

If execution is unavailable to the agent, follow the external execution handoff in [Execution Planning](references/execution-planning.md).

## Record the reviewed coverage

When the user accepts a round as complete, check whether the repository already maintains a record of data-quality coverage or known gaps.

- Update the existing record or create a concise record in the project's documentation location, such as `docs/data-quality-coverage.md`, when included in the authorized round. Do not ask again for documentation work already authorized; propose it if it remains outside the agreed scope.
- Record the review date or revision, scope, rules assessed, implementation status, synthetic test evidence, any authorized dataset evaluation and its result, execution environment, who ran the check, volume or partition scope, measured or estimated cost, privacy controls, remaining gaps, and limitations. Never record sensitive values or raw row examples.
- On later runs, use the record to guide discovery, but recheck current rules, tests, data scope, privacy classification, infrastructure, and costs. Do not treat the record as authoritative or current.

## Continue or finish

- After each completed round, ask whether the user wants another round, on the same or a different area.
- Keep each round focused and repeat the privacy, execution, and cost assessment when its scope or environment changes.
- When the user decides to stop, summarize rules reviewed and tests added or run, safe results, execution owner and environment, measured or estimated cost, remaining gaps, and unavailable checks. Do not continue without the user's choice.
