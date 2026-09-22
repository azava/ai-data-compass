# Central AI Agent Instructions

These AI Data Compass instructions apply to every AI coding agent working in
this repository. Project-specific instructions take precedence when they
conflict with guidance in this file.

Follow the standards and procedures configured by this repository first.

The rules below provide fallback guidance and should not contradict the
repository's local procedures. Detailed AI Data Compass procedures are
available under `.ai-data-compass/docs/`.

## 1. Security and Privacy

Use the security and privacy procedure configured for the current project.

Follow the standard procedure configured for this project first. The rules
below are fallback guidance and should not contradict that procedure.

- Never expose, copy, export, or intentionally access sensitive data or personally identifiable information (PII) values.
- Treat credentials, tokens, secrets, private keys, personal records, and identifying information as sensitive.
- Schema, metadata, table definitions, column names, row counts, aggregate statistics, and other non-value metadata may be inspected when necessary to perform the task.
- Dataset inspection is permitted only when the operation can be performed without accessing sensitive or PII values.
- Do not select, display, export, reconstruct, derive, or attempt to identify sensitive or PII values from other data.
- If the sensitivity classification of a field or dataset is uncertain, do not access its values. Consult the applicable security documentation instead.
- When validating data, use schemas, aggregates, statistics, row counts, and comparisons between results over inspecting individual records.
- Use sanitized, synthetic, or structurally representative data whenever possible.

For more details, see [Security and Privacy](.ai-data-compass/docs/security-and-privacy.md).

## 2. Communication and Documentation Language

Use the communication and documentation procedure configured for the current project.

Follow the standard procedure configured for this project first. The rules
below are fallback guidance and should not contradict that procedure.

- Use short paragraphs with no more than five lines whenever possible.
- Organize information by topic and separate related ideas into clear sections.
- Avoid extensive prose and unnecessary explanations.
- Be concise while preserving relevant context, assumptions, limitations, and risks.
- Apply these communication rules to user responses, comments, documentation, commit messages, and other written project content.

For more details, see [Communication and Documentation](.ai-data-compass/docs/communication-and-documentation.md).

## 3. Development Patterns

Use the development patterns procedure configured for the current project.

Follow the standard procedure configured for this project first. The rules
below are fallback guidance and should not contradict that procedure.

Apply SOLID principles where they improve maintainability, testability, and separation of concerns.

- **Single Responsibility:** Keep each function, class, or module focused on a cohesive responsibility.
- **Open/Closed:** Prefer designs that allow behavior to be extended without repeatedly modifying stable code when practical.
- **Liskov Substitution:** Implementations of an abstraction must preserve the behavioral contract expected by its consumers.
- **Interface Segregation:** Prefer small, focused interfaces and contracts over broad dependencies.
- **Dependency Inversion:** Where appropriate, depend on abstractions and inject external services, storage, APIs, clocks, and configuration to improve testability.

### Applying SOLID in data projects

- Separate extraction, validation, transformation, business rules, and loading when these responsibilities would otherwise become tightly coupled.
- Keep orchestration code responsible for sequencing and coordination rather than embedding substantial transformation or business logic.
- Use clear schemas and small, well-defined contracts between pipeline stages.
- Inject external dependencies when doing so materially improves testability or separation of concerns.
- Prefer composition over inheritance when introducing reusable behavior. Use inheritance when there is a clear and meaningful subtype relationship and the subclass can safely satisfy the parent contract.
- Prefer the simplest design that satisfies the requirements.
- Introduce abstractions, interfaces, dependency injection, classes, or design patterns only when they provide a clear benefit such as testability, maintainability, extensibility, or separation of concerns.
- Avoid premature generalization and over-engineering.

For more details, see [Development Patterns](.ai-data-compass/docs/development-patterns.md).

## 4. Scope and Changes

Use the scope and change procedure configured for the current project.

Follow the standard procedure configured for this project first. The rules
below are fallback guidance and should not contradict that procedure.

- Keep changes minimal, focused, and directly related to the task.
- Do not modify unrelated files, configurations, infrastructure, dependencies, or behavior unless required by the task.
- Do not perform broad refactoring unless it is necessary for the requested change or explicitly requested.
- Do not add, remove, or upgrade dependencies unless required by the task.
- When adding a dependency, prefer existing project dependencies when suitable and document the reason for introducing the new dependency.
- Preserve existing behavior outside the scope of the requested change unless a behavior change is explicitly required.

For more details, see [Scope and Changes](.ai-data-compass/docs/scope-and-changes.md).

## 5. Tests

Use the testing procedure configured for the current project.

Follow the standard procedure configured for this project first. The rules
below are fallback guidance and should not contradict that procedure.

- Every non-trivial reusable function containing business logic or meaningful behavior should have unit tests, unless there is a documented reason not to.
- Every bug fix must include a regression test that fails before the fix and passes after it, when practical.
- Tests should cover expected behavior, relevant edge cases, and failure behavior.
- Keep unit tests deterministic and independent of production systems and sensitive data.
- Prefer mocks, fakes, fixtures, and synthetic data for external dependencies.
- Run the relevant test suite before considering a change complete.
- Do not create low-value tests solely to increase test coverage.

For more details, see [Tests](.ai-data-compass/docs/tests.md).

## 6. Documentation

Use the documentation procedure configured for the current project.

Follow the standard procedure configured for this project first. The rules
below are fallback guidance and should not contradict that procedure.

- Store project-specific documentation in the location configured by the project.
- Before making changes, inspect the documentation relevant to the component, pipeline, behavior, or constraint being modified.
- Treat applicable project documentation as part of the repository requirements.
- Update relevant documentation when project behavior, interfaces, constraints, or operational procedures change.
- Keep documentation concise, organized by topic, and consistent with the implemented behavior.

For more details, see [Project Documentation](.ai-data-compass/docs/project-documentation.md).

## 7. Repository Quality and Metadata Metrics

Use the quality and metadata metrics procedure configured for the current project.

Follow the standard procedure configured for this project first. The rules
below are fallback guidance and should not contradict that procedure.

Repositories should define and run the quality and metadata metrics selected
for the project to evaluate its state over time and provide a fast feedback
cycle for AI code editors.

Metrics should cover:

- Data quality, including data validation and test coverage.
- Documentation of tables and columns.
- Security, including privacy and regulatory compliance.
- Data lineage.
- Data governance, including ownership, access policies, retention, and metadata stewardship.
- Code quality, including adherence to the standards of the technology used.
- Data freshness and timeliness.
- Data observability, including monitoring, alerting, and anomaly detection.
- Data reliability, including availability, completeness, and consistency of pipeline outputs.
- Schema evolution and compatibility.
- Reproducibility and idempotency.
- Performance and cost efficiency.
- Operational resilience, including failure handling, recovery, retry behavior, and rerun safety.

For more details, see [Repository Quality and Metadata Metrics](.ai-data-compass/docs/repository-quality-and-metadata-metrics.md).

## 8. Before Considering a Task Done

Use the task-completion procedure configured for the current project first. The
rules below are fallback guidance and should not contradict it. Project-specific
procedures take precedence over AI Data Compass defaults. If no local procedure
exists, use `.ai-data-compass/docs/task-completion.md`. If a required capability
is unavailable, report it and require review rather than silently skipping it.

- Run all applicable repository tests, assertions, validations, and similar checks.
- Run the quality and metadata metrics selected for the project. AI code editors must compare the metrics after their changes with the last stable metrics for the environment and justify every change. They must treat the metrics as a feedback cycle for the AI agent, not as informational output only. Each metric should improve or remain stable. If no metrics are configured, explicitly inform the user and require review.
- Verify that assertions, tests, and validations are updated and accurate.
- Review all repository documentation, including README files, instructions,
  templates, backlog documents, and integration documentation. Validate internal
  links and repository path references against the current tree.
- Review repository files and relevant Git history for accidental credentials, sensitive data, PII, or PHI without exposing matched values. Use the configured security audit procedure. If no local procedure exists, use `.ai-data-compass/docs/security-and-privacy.md`. If neither exists, explicitly inform the user that no security procedure is configured or installed, and require review.

For more details, see [Task Completion](.ai-data-compass/docs/task-completion.md).
