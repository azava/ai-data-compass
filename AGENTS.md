# Central AI Agent Instructions

These instructions apply to every AI coding agent working in this repository.

## 1. Security and Privacy

Project-specific security context: [`docs/security-and-privacy.md`](docs/security-and-privacy.md)

- Never expose, copy, export, or intentionally access sensitive data or personally identifiable information (PII) values.
- Treat credentials, tokens, secrets, private keys, personal records, and identifying information as sensitive.
- Schema, metadata, table definitions, column names, row counts, aggregate statistics, and other non-value metadata may be inspected when necessary to perform the task.
- Dataset inspection is permitted only when the operation can be performed without accessing sensitive or PII values.
- Do not select, display, export, reconstruct, derive, or attempt to identify sensitive or PII values from other data.
- If the sensitivity classification of a field or dataset is uncertain, do not access its values. Consult the applicable security documentation instead.
- When validating data, prefer schemas, aggregates, statistics, row counts, and comparisons between results over inspecting individual records.
- Prefer sanitized, synthetic, or structurally representative data whenever possible.

## 2. Communication and Documentation Language

Project-specific communication and documentation context: [`docs/communication-and-documentation.md`](docs/communication-and-documentation.md)

- Use short paragraphs with no more than five lines whenever possible.
- Organize information by topic and separate related ideas into clear sections.
- Avoid extensive prose and unnecessary explanations.
- Be concise while preserving relevant context, assumptions, limitations, and risks.
- Apply these communication rules to user responses, comments, documentation, commit messages, and other written project content.

## 3. Development Patterns

Project-specific development patterns: [`docs/development-patterns.md`](docs/development-patterns.md)

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

## 4. Scope and Changes

Project-specific scope and change guidance: [`docs/scope-and-changes.md`](docs/scope-and-changes.md)

- Keep changes minimal, focused, and directly related to the task.
- Do not modify unrelated files, configurations, infrastructure, dependencies, or behavior unless required by the task.
- Do not perform broad refactoring unless it is necessary for the requested change or explicitly requested.
- Do not add, remove, or upgrade dependencies unless required by the task.
- When adding a dependency, prefer existing project dependencies when suitable and document the reason for introducing the new dependency.
- Preserve existing behavior outside the scope of the requested change unless a behavior change is explicitly required.

## 5. Tests

Project-specific testing requirements: [`docs/tests.md`](docs/tests.md)

- Every non-trivial reusable function containing business logic or meaningful behavior should have unit tests, unless there is a documented reason not to.
- Every bug fix must include a regression test that fails before the fix and passes after it, when practical.
- Tests should cover expected behavior, relevant edge cases, and failure behavior.
- Keep unit tests deterministic and independent of production systems and sensitive data.
- Prefer mocks, fakes, fixtures, and synthetic data for external dependencies.
- Run the relevant test suite before considering a change complete.
- Do not create low-value tests solely to increase test coverage.

## 6. Documentation

Project-specific documentation requirements: [`docs/project-documentation.md`](docs/project-documentation.md)

- Store project-specific documentation in the `/docs` directory.
- Before making changes, inspect the documentation relevant to the component, pipeline, behavior, or constraint being modified.
- Treat applicable documentation in `/docs` as part of the repository requirements.
- Update relevant documentation when project behavior, interfaces, constraints, or operational procedures change.
- Keep documentation concise, organized by topic, and consistent with the implemented behavior.

## 7. Repository Quality and Metadata Metrics

Project-specific repository quality and metadata metrics context: [`docs/repository-quality-and-metadata-metrics.md`](docs/repository-quality-and-metadata-metrics.md)

Repositories should implement quality and metadata metrics to evaluate their state over time and provide a fast feedback cycle for AI code editors.

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

## 8. Before Considering a Task Done

Project-specific completion checklist: [`docs/task-completion.md`](docs/task-completion.md)

 - Run all applicable repository tests, assertions, validations, and similar checks.
 - Run the Repository Quality and Metadata Metrics. AI code editors should compare the metrics after their changes with the last stable metrics for the environment. Each metric should improve or remain stable; AI code editors must justify every change.
 - Verify that assertions, tests, and validations are updated and accurate.
 - Review that documentation is updated and accurate.
 - Review repository files and relevant Git history for accidental credentials, sensitive data, PII, or PHI without exposing matched values. Use the `security-audit` skill as part of this review; if the agent cannot open or invoke the skill directly, read and follow `.agents/skills/security-audit/SKILL.md`.
