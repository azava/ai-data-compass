---
name: project-quality-metrics
description: Define and implement project quality metrics and baseline comparisons.
---

# Project Quality Metrics

Help the user select, define, implement, and review a useful set of quality metrics for code, repositories, data metadata, and infrastructure. Start with the simplest approach that fits the project, then improve it in focused rounds. This skill does not replace code-behavior tests or data-quality tests.

## Privacy and access boundaries

Apply these safeguards throughout discovery, implementation, execution, comparison, and reporting:

- Establish what data and metadata may be inspected before reading values or connecting to external systems. Never expose credentials, secrets, PII, PHI, personal records, or sensitive metric values.
- Prefer repository configuration, schemas, aggregate results, and synthetic examples. Treat metadata as potentially sensitive when it reveals protected business or operational details.
- Do not request credentials in chat or store them in metric files, logs, CI artifacts, or reports. Use only access already authorized for the task.
- If a metric would require prohibited or uncertain access, do not collect it; explain the gap and propose a safe source or aggregate instead.

## Discover the current state

- Confirm or infer the scope: whole project, selected components, or a particular environment. State the scope and ask only when ambiguity could change the recommended metrics.
- Read the project's metric inventory, instructions, relevant code and documentation, CI configuration, existing metric definitions, dashboards or output locations that are available in the repository.
- Use `.ai-data-compass/docs/repository-quality-and-metadata-metrics.md` as a starting inventory when it is available; also consider project-specific categories and existing sources.
- Identify relevant languages, platforms, execution tools, existing collections, baselines, review cadence, and owners from available evidence. Do not assume that a source or service is absent just because it is not documented in the repository.
- The metric inventory may include code quality and tests, repository and pipeline reliability, data quality, observability, metadata documentation, lineage, security and privacy, reproducibility, performance, and cost. Select only categories that help this project.
- For table and column documentation, consider measurable coverage and freshness, such as the share of required descriptions present and current. Assessing correctness or usefulness may require a business definition or catalog that is outside the repository; ask for that context only if it affects the selected metric.
- Present a concise map of configured metrics, promising gaps, and unknowns. Keep external context questions limited to information that could change the next recommendation.

## Recommend a focused round

- Offer three useful choices tailored to the findings, briefly explain each, and recommend one. Let the user select an area or propose another.
- If nothing exists, propose a few useful metrics with a simple runner and local history, using CI when suitable. If a system already exists, improve it incrementally.
- Introduce more infrastructure only when a concrete need warrants it, such as retention, access controls, scale, or alerts. Ask only for information that changes the selected round.
- Agree on the round's outcome before implementation, then iterate with the user until it is accepted. Reuse existing tools and authorization; obtain agreement for new infrastructure, dependencies, external access, or ongoing cost.

## Define and collect

For each selected metric, define enough context to interpret it consistently:

- A stable name or ID, purpose, formula, unit, scope, dimensions, source, and collection method.
- The responsible owner, target or acceptable range, thresholds when needed, and review cadence.
- The execution trigger and environment, expected cost or resource use, failure behavior, and privacy/retention constraints.

Propose initial settings from available project context and label assumptions and pending decisions. Missing owners, targets, or review schedules should not block a safe, authorized first collection. Resolve uncertainty that affects access, privacy, cost, or meaningful interpretation before executing; do not invent thresholds or report compliance with undefined targets.

### Execution

- Provide one entry point for the selected suite, such as a Python script when it fits the project, or an existing native command. Default to reporting safe results without persisting them; use an explicit `--save` option or equivalent for historical records. Use scratch locations for temporary output.
- When defining history storage or baseline promotion, read [Metric History Format](references/metric-history.md). Operational history may include regressions and failed collections with explicit statuses; saving a run does not make it a stable baseline.
- Choose triggers appropriate to the source: CI for repository measurements, and deployment events, schedules, or pipeline completion for current environment or data measurements. Identify who or what runs the suite and saves results.
- Implement and run the agreed collection path when authorized and available. Report commands, results, assumptions, and failed, skipped, or unavailable checks. Distinguish implemented collectors from measurements actually executed.
- Use existing monitoring for actionable alerts when needed; add alerting only within the agreed scope.

## Save the metric state

- After the user accepts a round, update the existing metric registry or documentation with definitions, execution and storage choices, baseline state, evidence, and remaining gaps. If none exists, include a concise project-local record in the agreed work.
- Keep run results in the history store and setup decisions in documentation.
- On later runs, use the record to accelerate discovery, but recheck current sources, configuration, privacy boundaries, and measurements.

## Use the suite for agent feedback

Once the suite is ready, use it as feedback after relevant development changes:

- Run the suite in its default reporting mode and compare results with the latest stable baseline for the same environment and compatible scope, metric definitions, and data context.
- Explain each change as an improvement, regression, expected effect, or measurement difference. Investigate regressions instead of accepting them solely because collection succeeded.
- If a compatible baseline is unavailable, report the limitation and define how to establish one. Do not claim an incomparable result improved or preserved quality.

## Continue or finish

- After each accepted round, ask whether the user wants another round, wants to finish, or wants to move on to another skill. Continue only with their choice; offer three tailored options for another round.
- When finishing, summarize implemented metrics, execution and storage locations, results, baseline status, and remaining gaps. Do not invoke another skill automatically.
